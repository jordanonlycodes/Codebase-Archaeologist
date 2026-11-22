"""Indexed, conservative name resolution; no imports, preprocessing or execution."""
from pathlib import PurePosixPath
import posixpath


class Symbols:
    def __init__(self, facts, paths):
        self.facts = facts
        self.paths = set(paths)
        self.c_global = {}
        self.modules = {}
        self.file_modules = {}
        self.headers = {}
        self._module_cache = {}
        self._include_cache = {}
        self.c_local = {}
        for path in sorted(paths):
            for offset in range(len(PurePosixPath(path).parts)):
                suffix = '/'.join(PurePosixPath(path).parts[offset:])
                self.headers.setdefault(suffix,[]).append(path)
            if path.endswith(('.py','.pyi')):
                parts = list(PurePosixPath(path).with_suffix('').parts)
                if parts[-1] == '__init__':
                    parts.pop()
                names = {'.'.join(parts)} if parts else set()
                # Package chains evidence an import root outside that package.
                parent = PurePosixPath(path).parent
                while parent.as_posix() != '.' and (parent/'__init__.py').as_posix() in self.paths:
                    parent = parent.parent
                offset = 0 if parent.as_posix()=='.' else len(parent.parts)
                if offset < len(parts) and offset < len(PurePosixPath(path).parent.parts):
                    names.add('.'.join(parts[offset:]))
                # src is a candidate source root, not an assertion about sys.path.
                if parts and parts[0]=='src' and len(parts)>1:
                    names.add('.'.join(parts[1:]))
                self.file_modules[path] = sorted(names)
                for name in names:
                    self.modules.setdefault(name,[]).append(path)
        for fact in facts.values():
            if fact.language == 'C':
                for name, ids in fact.definitions.items():
                    self.c_global.setdefault(name,[]).extend(i for i in ids if i not in fact.static)
                    self.c_local[(fact.path,name)] = self.choose(ids)
        self.c_global = {name:self.choose(ids) for name,ids in self.c_global.items()}

    @staticmethod
    def choose(candidates):
        values = sorted(set(candidates))
        return (values[0], 'resolved_internal') if len(values)==1 else (None,'ambiguous' if values else 'unresolved')

    def module(self, path, name, level=0):
        key = (path,name,level)
        if key not in self._module_cache:
            self._module_cache[key] = self._module(path,name,level)
        return self._module_cache[key]

    def _module(self, path, name, level):
        if not level:
            return self.choose(self.modules.get(name,()))
        candidates = []
        for current in self.file_modules.get(path,()):
            package = current.split('.') if PurePosixPath(path).stem=='__init__' else current.split('.')[:-1]
            if level > len(package):
                continue
            parts = package[:len(package)-level+1]
            qualified = '.'.join(parts+([name] if name else []))
            candidates.extend(self.modules.get(qualified,()))
        return self.choose(candidates)

    def include(self, path, name, mode):
        key = (path,name,mode)
        if key not in self._include_cache:
            self._include_cache[key] = self._include(path,name,mode)
        return self._include_cache[key]

    def _include(self, path, name, mode):
        if mode == 'dynamic' or not name or '\\' in name or name.startswith('/'):
            return None,'unsupported_dynamic'
        if mode == 'quoted':
            local = posixpath.normpath(posixpath.join(posixpath.dirname(path),name))
            if local in self.paths:
                return local,'resolved_internal'
        # No compiler search path guessing: a unique repository suffix is evidence
        # for a candidate include; duplicate suffixes explicitly remain ambiguous.
        candidates = self.headers.get(name,())
        return self.choose(candidates)

    def import_target(self, path, module, symbol, level):
        base,status = self.module(path,module,level)
        if status == 'ambiguous' or symbol in {'','*'}:
            return base,status
        child,child_status = self.module(path,'.'.join(filter(None,[module,symbol])),level)
        if child_status == 'ambiguous':
            return None,'ambiguous'
        if child:
            base_facts = self.facts.get(base)
            if base_facts and symbol in base_facts.scopes[0].bindings:
                return None,'ambiguous'
            return child,'resolved_internal'
        return base,status

    def binding(self, facts, scope_id, name):
        while scope_id is not None:
            scope = facts.scopes[scope_id]
            if scope.wildcard:
                return None, 'unsupported_dynamic'
            entries = scope.bindings.get(name,())
            if entries:
                if len(entries)>1:
                    return None,'ambiguous'
                if entries[0][0] == 'dynamic':
                    return None,'unsupported_dynamic'
                return entries[0],'resolved_internal'
            scope_id = scope.parent
        return None,'unresolved'

    def python_call(self, facts, ref):
        if ref.name == '<dynamic expression>':
            return None,'unsupported_dynamic'
        pieces = ref.name.split('.')
        bound,status = self.binding(facts,ref.scope,pieces[0])
        if bound is None:
            return None,status if len(pieces)==1 else 'unsupported_dynamic'
        if bound[0]=='function':
            return (bound[1],'resolved_internal') if len(pieces)==1 else (None,'unsupported_dynamic')
        _,module,symbol,level = bound
        if symbol:
            if len(pieces)>1:
                base,base_status = self.module(facts.path,module,level)
                if base_status=='ambiguous':
                    return None,base_status
                if base in self.facts and symbol in self.facts[base].scopes[0].bindings:
                    return None,'unsupported_dynamic'
                # from pkg import sub; sub.func: resolve an actual submodule only.
                module = module+'.'+symbol if module else symbol
                symbol = '.'.join(pieces[1:])
        else:
            if len(pieces)==1:
                return None,'unsupported_dynamic'
            module = '.'.join([module,*pieces[1:-1]])
            symbol = pieces[-1]
        path,status = self.module(facts.path,module,level)
        if path is None:
            return None,status
        target_facts = self.facts.get(path)
        if target_facts is None or '.' in symbol:
            return None,'unresolved'
        target,status = self.binding(target_facts,0,symbol)
        # Re-exports and arbitrary assignment aliases intentionally stay unresolved.
        if target is not None and target[0]=='function':
            return target[1],'resolved_internal'
        return None, status if target is None else 'unsupported_dynamic'

    def c_call(self, facts, ref, declarations, macros, static_declarations):
        if ref.mode != 'direct' or ref.name in macros or ref.name in facts.shadowed.get(ref.source,()):
            return None,'unsupported_dynamic'
        same = self.c_local.get((facts.path,ref.name))
        if same is not None:
            return same
        if ref.name not in declarations or ref.name in static_declarations:
            return None,'unresolved'
        return self.c_global.get(ref.name,(None,'unresolved'))
