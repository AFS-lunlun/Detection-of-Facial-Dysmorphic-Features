"""Optional figures generated only from supplied predictions or hypothetical scenarios."""
from pathlib import Path


def setup():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    return plt


def save(fig, folder, stem):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'pdf', 'svg'):
        fig.savefig(folder / (stem + '.' + ext), dpi=300, bbox_inches='tight')


def evaluation_plots(folder, roc, m, calibration, synthetic=False):
    plt = setup()
    title = 'Synthetic demonstration — ' if synthetic else ''
    fig, ax = plt.subplots(figsize=(3.4, 3.1))
    ax.plot([p['fpr'] for p in roc], [p['tpr'] for p in roc], color='#328782', lw=1.6)
    ax.plot([0,1],[0,1], '--', color='.6', lw=.8)
    ax.set(xlim=(0,1), ylim=(0,1.02), xlabel='False-positive rate', ylabel='True-positive rate',
           title=title + 'ROC')
    if m['auc'] is not None:
        ax.text(.97,.05, f"AUC = {m['auc']:.4f}", transform=ax.transAxes, ha='right')
    save(fig, folder, 'roc'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(3.7,3.3))
    cm = [[m['tn'], m['fp']], [m['fn'], m['tp']]]
    ax.imshow(cm, cmap='Blues', vmin=0, vmax=max(max(r) for r in cm) or 1)
    for y in (0,1):
        for x in (0,1):
            v=cm[y][x]
            ax.text(x,y,str(v),ha='center',va='center',color='white' if v>max(max(r) for r in cm)/2 else 'black')
    ax.set_xticks([0,1], ['Reference','Positive'])
    ax.set_yticks([0,1], ['Reference','Positive'])
    ax.set(xlabel='Predicted class',ylabel='True class',title=title+'Confusion matrix')
    save(fig, folder, 'confusion_matrix'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(3.4,3.1))
    nonempty = [r for r in calibration if r['count']]
    ax.plot([r['mean_probability'] for r in nonempty], [r['positive_fraction'] for r in nonempty],
            'o-', color='#52658A')
    ax.plot([0,1],[0,1],'--',color='.6',lw=.8)
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean predicted probability',ylabel='Observed positive fraction',
           title=title+'Calibration')
    save(fig, folder, 'calibration'); plt.close(fig)


def comparison(folder, reports):
    plt=setup()
    keys=['accuracy','precision','sensitivity','f1','auc']
    titles=['Accuracy','Precision','Sensitivity','F1-score','AUC']
    fig, axes=plt.subplots(1,5,figsize=(9.2,2.9))
    colors=['#52658A','#328782','#7AA883']
    for ax,key,title in zip(axes,keys,titles):
        for i,(name,r) in enumerate(reports):
            v=r['metrics'][key]
            if v is not None:
                ax.bar(i,v,color=colors[i%3],width=.65)
                ax.text(i,v+.02,f'{v:.3f}',ha='center',fontsize=6)
        ax.set_ylim(0,1.12)
        ax.set_xticks(range(len(reports)),[name for name,_ in reports],rotation=45,ha='right')
        ax.set_title(title)
    if any(r.get('data_kind')=='synthetic' for _,r in reports):
        fig.suptitle('Synthetic demonstration')
    fig.tight_layout()
    save(fig,folder,'metric_comparison');plt.close(fig)
