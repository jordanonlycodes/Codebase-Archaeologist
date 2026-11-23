"""Print-sized report charts derived only from saved Task7C.0 JSON; no refits."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OPT=ROOT/'reports/ml/optimization/task7c0-v1'
def charts(out):
    result=json.loads((OPT/'results.json').read_text());protocol=json.loads((OPT/'protocol.json').read_text())
    short={'v1_hgb_baseline':'HGB11 baseline','v1_hgb_regularized':'HGB11 regularized','v1_lr_balanced_c10':'LR11 balanced C10',
      'v1_lr_unweighted_c01':'LR11 unweighted C0.1','v1_rf_baseline':'RF11 baseline','v1_rf_deeper_unweighted':'RF11 deeper unweighted',
      'v2_extra_trees':'Extra Trees22','v2_hgb_regularized':'HGB22 regularized','v2_lr_balanced':'LR22 balanced',
      'v2_rf_baseline_shape':'RF22 baseline shape','v2_rf_deeper_unweighted':'RF22 deeper unweighted'}
    def save(fig,name):fig.tight_layout();fig.savefig(out/name,dpi=220);plt.close(fig)
    with plt.rc_context({'font.size':8.5,'axes.spines.top':False,'axes.spines.right':False}):
        names=list(protocol['configurations']);rows=[json.loads((OPT/(n+'.json')).read_text()) for n in names]
        fig,ax=plt.subplots(figsize=(6.6,4.4));ax.barh([short[n] for n in names],[r['cv_mean_f1'] for r in rows],xerr=[r['cv_std_f1'] for r in rows],color='#7A1E2B')
        ax.set(xlabel='Mean fold F1 at 0.5; error bars = fold SD',title='Training-only grouped CV (3 folds, seed42)');save(fig,'cv_print.png')
        names=list(result['finalists']);labels=['Original RF11']+[short[n] for n in names]+['Always positive']
        values=[result['baseline_validation']]+[result['finalists'][n]['validation'] for n in names]+[result['always_positive_validation']]
        half=[result['baseline_validation']]+[result['finalists'][n]['validation_at_half'] for n in names]+[result['always_positive_validation']]
        fig,ax=plt.subplots(figsize=(6.6,4.6));y=np.arange(len(labels));ax.barh(y-.23,[r['f1'] for r in values],height=.22,label='F1: OOF operating threshold',color='#7A1E2B');ax.barh(y,[r['f1'] for r in half],height=.22,label='F1: fixed 0.5',color='#b8969d');ax.barh(y+.23,[r['roc_auc'] for r in values],height=.22,label='ROC-AUC',color='#526d70')
        ax.set_yticks(y,labels);ax.set_ylim(-.5,len(labels)+2);ax.set(xlabel='Observed metric',title='Reused official validation (n=2,723), not blind test');ax.legend(loc='upper right',fontsize=7.5);save(fig,'validation_print.png')
        fig,ax=plt.subplots(figsize=(6.6,4.6))
        for name in names:
            row=json.loads((OPT/(name+'.json')).read_text())['threshold_selection'];grid=row['grid'];ax.plot([r['threshold'] for r in grid],[r['f1'] for r in grid],marker='.',label=short[name]);chosen=next(r for r in grid if r['threshold']==row['operating']);ax.scatter(chosen['threshold'],chosen['f1'],marker='x',s=40)
        ax.set(xlabel='Predefined threshold',ylabel='Pooled training OOF F1',title='OOF threshold development; × = operating choice');ax.legend(fontsize=7.5,ncol=2);save(fig,'threshold_print.png')
        fig,ax=plt.subplots(figsize=(6.6,4.5))
        for i,(label,row) in enumerate(zip(labels,values)):
            ax.scatter(row['recall'],row['precision'],s=40,marker='x' if i==0 else 'o',label=label)
        ax.set(xlabel='Recall',ylabel='Precision',xlim=(0,1.05),ylim=(.35,.65),title='Validation operating points, not full PR curves');ax.legend(fontsize=7.5,loc='upper right');save(fig,'precision_recall_print.png')
