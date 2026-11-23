"""Regenerate Task7C.0 scientific figures from saved development evidence only."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve,precision_recall_curve

OUT=Path('reports/ml/optimization/task7c0-v1');CACHE=Path('artifacts/devign-optimization/task7c0-v1')
def read(name):return json.loads((OUT/name).read_text())
def save(fig,name):
    fig.tight_layout();fig.savefig(OUT/name,dpi=160);plt.close(fig)


def main():
    results=read('results.json');protocol=read('protocol.json');finals=results['finalists'];names=list(finals)
    cv=[read(n+'.json') for n in protocol['configurations']]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(11,6));ax.barh([r['name'] for r in cv],[r['cv_mean_f1'] for r in cv],xerr=[r['cv_std_f1'] for r in cv],color='#81515b')
    ax.set(xlabel='Mean fold F1 at threshold0.5 (bars ± fold SD, not confidence interval)',title='Training-only 3-fold grouped CV · seed42 · task7c0-v1');save(fig,'cv_comparison.png')
    fig,ax=plt.subplots(figsize=(11,6));labels=['Original RF/.5']+names+['Always positive'];values=[results['baseline_validation']]+[finals[n]['validation'] for n in names]+[results['always_positive_validation']]
    half=[results['baseline_validation']]+[finals[n]['validation_at_half'] for n in names]+[results['always_positive_validation']]
    y=np.arange(len(labels));ax.barh(y-.24,[m['f1'] for m in values],height=.23,label='F1, OOF operating threshold',color='#81515b');ax.barh(y,[m['f1'] for m in half],height=.23,label='F1, fixed threshold 0.5',color='#baa1a7');ax.barh(y+.24,[m['roc_auc'] for m in values],height=.23,label='ROC-AUC',color='#567578');ax.set_yticks(y,labels);ax.legend(fontsize=8,loc='lower right');ax.set(xlabel='Observed development metric',title='Official cleaned validation (n=2723); not blind test');save(fig,'validation_comparison.png')
    fig,ax=plt.subplots(figsize=(10,6))
    for name in names:
        row=read(name+'.json')['threshold_selection'];points=row['grid'];ax.plot([p['threshold'] for p in points],[p['f1'] for p in points],marker='.',label=name)
        chosen=next(p for p in points if p['threshold']==row['operating']);ax.scatter(chosen['threshold'],chosen['f1'],marker='x',s=60)
    ax.set(xlabel='Predefined score threshold',ylabel='Pooled training OOF F1',title='Threshold development: grouped training OOF only; × = operating choice');ax.legend(fontsize=8,ncol=2);save(fig,'oof_thresholds.png')
    baseline=np.load(CACHE/'baseline-validation.npz',allow_pickle=False);labels=baseline['labels'];fig,axes=plt.subplots(1,2,figsize=(13,5))
    for name,prob in [('Original RF',baseline['probabilities'])]+[(n,np.load(CACHE/(n+'-validation.npy'),allow_pickle=False)) for n in names]:
        fpr,tpr,_=roc_curve(labels,prob);precision,recall,_=precision_recall_curve(labels,prob);axes[0].plot(fpr,tpr,label=name);axes[1].plot(recall,precision,label=name)
    axes[0].plot([0,1],[0,1],'k--',linewidth=.8);axes[0].set(xlabel='False positive rate',ylabel='True positive rate',title='ROC: reused official validation')
    axes[1].axhline(np.mean(labels),color='k',linestyle='--',linewidth=.8);axes[1].set(xlabel='Recall',ylabel='Precision',title='PR: reused official validation; dashed = prevalence')
    axes[1].legend(fontsize=7);save(fig,'validation_curves.png')
    winner=results['highest_validation_f1'];fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,title,row in zip(axes,['Original RF, .5',winner+', '+str(finals[winner]['threshold'])],[results['baseline_validation'],finals[winner]['validation']]):
        matrix=np.array(row['confusion_matrix']);ax.imshow(matrix,cmap='Greys',vmin=0,vmax=matrix.max());ax.set_xticks([0,1],['Predicted0','Predicted1']);ax.set_yticks([0,1],['Actual0','Actual1']);ax.set_title(title,fontsize=9)
        for i in range(2):
            for j in range(2):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>.65*matrix.max() else 'black')
    fig.suptitle('Confusion matrices — cleaned validation n=2723; candidate is not deployment endorsement',fontsize=10);save(fig,'validation_confusions.png')
    with np.load('data/processed/devign-v1/development.npz',allow_pickle=False) as data:
        counts=np.array([[np.sum(data['y_'+split]==c) for c in [0,1]] for split in ['train','validation']])
    fig,ax=plt.subplots(figsize=(7,5));x=np.arange(2)
    for c,color in [(0,'#567578'),(1,'#81515b')]:
        bars=ax.bar(x+(c-.5)*.3,counts[:,c],width=.3,label=f'Class{c}',color=color);ax.bar_label(bars,padding=3)
    ax.set_xticks(x,['Cleaned training','Cleaned validation']);ax.set(ylabel='Function rows',title='Development label distribution · official test not used');ax.legend();save(fig,'development_classes.png')
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.png')}
    (OUT/'figures.json').write_text(json.dumps({'source_results_sha256':hashlib.sha256((OUT/'results.json').read_bytes()).hexdigest(),'files':files,'test_predictions':0},indent=2)+'\n')
    print('Generated',len(files),'genuine development figures')
if __name__=='__main__':main()
