"""Safe GitHub response accounting and cooldowns; no credentials or upstream body logs."""
from collections import OrderedDict
from copy import deepcopy
from datetime import timezone
from email.utils import parsedate_to_datetime
import re
import threading
import time
from app.errors import AnalysisError


def number(value, maximum=1_000_000_000):
    return int(value) if isinstance(value,str) and re.fullmatch(r'\d{1,12}',value) and int(value)<=maximum else None


def response_metadata(headers, now):
    retry=number(headers.get('retry-after'),2_147_483_647)
    if retry is None and headers.get('retry-after'):
        try:
            date=parsedate_to_datetime(headers['retry-after'])
            if date.tzinfo is not None:retry=max(0,int(date.timestamp()-now)+1)
        except (ValueError,TypeError,OverflowError):pass
    safe=lambda name,pattern: headers.get(name) if re.fullmatch(pattern,headers.get(name,'')) else None
    return dict(limit=number(headers.get('x-ratelimit-limit')),
                remaining=number(headers.get('x-ratelimit-remaining')),
                reset_at=number(headers.get('x-ratelimit-reset'),253402300799),
                resource=safe('x-ratelimit-resource',r'[a-z_]{1,32}'),
                request_id=safe('x-github-request-id',r'[A-Za-z0-9:_-]{1,128}'),
                retry_after=retry, observed_at=int(now))


class HistoryAPIError(AnalysisError):
    def __init__(self,message,code,status,api):
        super().__init__(message,code,status);self.api=api


class RateLedger:
    def __init__(self,clock=time.time):
        self.clock=clock;self.lock=threading.RLock();self.records=OrderedDict()

    def status(self,scope):
        with self.lock:
            return deepcopy(self.records.get(scope,{'state':'unknown'}))

    def before(self,scope):
        meta=self.status(scope)
        if meta.get('retry_at',0)>self.clock():
            meta['retry_after']=max(1,int(meta['retry_at']-self.clock())+1)
            raise HistoryAPIError('GitHub requests are cooling down. Previously loaded evidence remains available; retry after the reported cooldown.',
                                  'github_rate_limit',429,meta)

    def record(self,scope,headers,status,body):
        now=self.clock();meta=response_metadata(headers,now);message=body.get('message','') if isinstance(body,dict) else ''
        message=message.lower() if isinstance(message,str) else ''
        kind=None
        if status in (403,429) or status==200 and meta['remaining']==0:
            if meta['remaining']==0 or 'api rate limit exceeded' in message:kind='primary'
            elif meta['retry_after'] is not None or 'secondary rate limit' in message or 'abuse detection' in message:kind='secondary'
            elif status==429:kind='unspecified'
        meta['state']='limited' if kind else 'connected' if status==200 else 'unavailable'
        if kind:
            until=max([now+60 if meta['retry_after'] is None and not (meta['remaining']==0 and meta['reset_at'] and meta['reset_at']>now) else now,
                       now+(meta['retry_after'] or 0),meta['reset_at'] if meta['remaining']==0 and meta['reset_at'] else now])
            meta.update(kind=kind,retry_at=int(until),cooldown_source='reported' if meta['retry_after'] is not None or meta['remaining']==0 and meta['reset_at'] and meta['reset_at']>now else 'conservative_backoff')
        with self.lock:
            previous=self.records.get(scope,{})
            # A response already in flight must not shorten an observed cooldown.
            if previous.get('retry_at',0)>now:
                meta.update(state='limited',kind=previous['kind'],retry_at=max(previous['retry_at'],meta.get('retry_at',0)),cooldown_source=previous['cooldown_source'])
            self.records[scope]=meta;self.records.move_to_end(scope)
            while len(self.records)>8:self.records.popitem(last=False)
        if status==200:return
        if kind:
            label='primary API allowance' if kind=='primary' else 'request activity' if kind=='secondary' else 'API requests'
            raise HistoryAPIError(f'GitHub is temporarily limiting {label}. Previously loaded history remains available. Retry after the reported cooldown; success is not guaranteed.', 'github_rate_limit',429,meta)
        if status==401:raise HistoryAPIError('GitHub API authentication failed. Check server configuration.', 'github_authentication',502,meta)
        if status==403:raise HistoryAPIError('GitHub denied access to this repository.', 'github_forbidden',403,meta)
        if status==404:raise HistoryAPIError('Public repository or revision was not found or is inaccessible.', 'github_unavailable',404,meta)
        if status==409:raise HistoryAPIError('No Git history is available for this repository.', 'github_empty',422,meta)
        raise HistoryAPIError('GitHub could not provide history evidence. Retry later; previously loaded data remains available.', 'github_upstream',502,meta)
