#!/usr/bin/env python3
"""Reproduce the measured TensorForge area/support catalogue.

The four adjacent CSV snapshots are sufficient for an offline rebuild.  Use
--refresh --repo-root PATH to repeat the documented canonical source selection.
No model or sum of component areas is used in any measured panel.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

HERE = Path(__file__).resolve().parent
STEM = 'precision_area_sweep'
FAMILIES = ('TF32', 'FP16', 'BF16', 'FP8', 'FP6', 'FP4', 'INT8', 'INT4', 'Binary')
MODES = ('TF32', 'FP16', 'BF16', 'FP8 (E4M3)', 'FP8 (E5M2)',
         'FP6 (E3M2)', 'FP6 (E2M3)', 'FP4 (E2M1)', 'INT8', 'INT4', 'Binary (1 bit)')
EXTRAS = ('MX scaling', 'NV scaling', 'FP4 LUT', 'Packed 2×FP4')
COLORS = {1:'#9FBAD4', 2:'#F0C38E', 3:'#ECC7A6', 4:'#E9ABA5', 5:'#AACBCF',
          6:'#AEC6A0', 7:'#B9AFCD', 9:'#D9BD9C'}
ACCENT = '#BF5742'
FULL = 'tensorforge_site_bundle/data/area_power_measurements.csv'
DP = 'tensorforge_site_bundle/data/dp_training.csv'


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def number_equal(value, expected):
    return bool(value) and float(value) == expected


def support(precision):
    if precision in ('4', '8'):
        return ['Binary']
    return [family for family in FAMILIES[:-1] if family in precision]


def modes(families):
    result = []
    for family in families:
        result.extend({'FP8':['FP8 (E4M3)', 'FP8 (E5M2)'],
                       'FP6':['FP6 (E3M2)', 'FP6 (E2M3)'],
                       'FP4':['FP4 (E2M1)'], 'Binary':['Binary (1 bit)']}.get(family, [family]))
    return result


def enrich(row):
    row = dict(row)
    families = support(row['precision_set'])
    row['supported_families'] = ';'.join(families)
    row['supported_modes'] = ';'.join(modes(families))
    row['numeric_mode_count'] = str(len(modes(families)))
    row['mx_scaling'] = str(int(row['precision_set'].startswith('MX')))
    row['nv_scaling'] = str(int('NV' in row['precision_set']))
    row['lut'] = str(int('LUT' in row['precision_set']))
    row['packed_2xfp4'] = str(int('2FP4' in row['precision_set']))
    row['display_label'] = ('Binary1bit (norm' + row['norm_kind'] + ')'
                            if families == ['Binary'] else row['precision_set'])
    return row


def refresh(repo_root, dim_k, clock_mhz):
    sources = {}
    for name in (DP, FULL):
        rows = read_csv(repo_root / name)
        sources[name] = [dict(row, source_file=name, source_row=str(i))
                         for i, row in enumerate(rows, 2)]
    candidates = [row for row in sources[FULL]
                  if number_equal(row['dimK'], dim_k)
                  and number_equal(row['clk_mhz'], clock_mhz)
                  and row['design_name'] != 'DotProduct_baseline']
    dp_rows = [row for row in sources[DP]
               if number_equal(row['dimK'], dim_k)
               and number_equal(row['clk_mhz'], clock_mhz)]
    # The curated dp table fixes canonical synthesis settings, not minimum area.
    chosen = {row['precision_set']: row for row in dp_rows}
    mixed = []
    for precision in sorted(set(row['precision_set'] for row in candidates)):
        subset = [row for row in candidates if row['precision_set'] == precision]
        if subset[0]['design_name'] == 'DotProductWrapperFP16INT':
            # These names describe asymmetric operands, not selectable modes.
            unique = {row['variant']:row for row in reversed(subset)}
            assert len(unique) == 1, (precision, list(unique))
            mixed.append(dict(next(iter(unique.values())),
                              display_label=precision.replace('INT', ' × INT')))
            continue
        if precision in chosen:
            continue
        if precision in ('4', '8'):
            desired_mid = '0'
        elif precision in ('FP4', 'FP4LUT', 'MXFP4', 'MXFP4LUT',
                           'NVFP4', 'NVFP4LUT', 'MXNVFP4', 'MXNVFP4LUT'):
            desired_mid = '9'
        elif precision in ('FP8', 'FP8FP6FP4'):
            desired_mid = '22'
        elif precision == 'FP6':
            desired_mid = '17'
        else:
            desired_mid = '26'
        subset = [row for row in subset if row['midMat'] == desired_mid]
        if precision not in ('4', '8', 'INT4', 'INT8', 'INT8INT4'):
            subset = [row for row in subset if row['norm_kind'] == 'FP32'
                       and row['acc_kind'] == 'FP32' and row['out_kind'] == 'FP32']
        assert subset, (precision, desired_mid)
        # Prefer explicitly spelled noNV aliases where present, then source order.
        subset.sort(key=lambda row: ('noNV' not in row['variant'], int(row['source_row'])))
        selected = dict(subset[0])
        selected['equivalent_source_rows'] = ';'.join(
            row['source_row'] for row in subset[1:]
            if row['area_value'] == selected['area_value'])
        chosen[precision] = selected
    rows = [enrich(row) for row in chosen.values()]
    rows.sort(key=lambda row:(int(row['numeric_mode_count']), float(row['area_value']), row['precision_set']))
    for i,row in enumerate(rows,1): row['column_id'] = f'U{i:02d}'
    mixed.sort(key=lambda row: row['precision_set'])
    arrays = []
    for precision in ('BF16', 'FP16', 'TF32', 'FP32'):
        subset = [row for row in sources[FULL]
                  if row['design_name'] == 'OuterProductArray'
                  and number_equal(row['clk_mhz'], clock_mhz)
                  and row['variant'] == f'{precision}_dimK1_noMX_normFP32_accFP32_outFP32_midMat26_m8_n8']
        assert len(subset)==1, (precision, len(subset))
        arrays.append(dict(subset[0], display_label=precision))
    additional = []
    for precision in ('FP8FP62FP4', 'MXFP8FP6FP4'):
        subset = [row for row in sources[FULL]
                  if row['precision_set']==precision
                  and number_equal(row['dimK'],32)
                  and number_equal(row['clk_mhz'],clock_mhz)]
        assert subset and len({r['variant'] for r in subset})==1
        selected=enrich(subset[0])
        selected['equivalent_source_rows']=';'.join(r['source_row'] for r in subset[1:])
        selected['display_label']=('FP8 + FP6\n+ 2×FP4' if precision=='FP8FP62FP4'
                                   else 'MXFP8 + FP6\n+ FP4')
        additional.append(selected)
    assert len(rows)==31 and len(mixed)==4 and len(arrays)==4 and len(additional)==2
    return rows,mixed,arrays,additional


def validate(rows, mixed, arrays, additional):
    assert len(rows)==31 and len(mixed)==4 and len(arrays)==4
    assert len({r['column_id'] for r in rows})==31
    assert all(r['design_name'] not in ('DotProductWrapperFP16INT','DotProduct_baseline') for r in rows)
    assert set().union(*(set(r['supported_families'].split(';')) for r in rows))==set(FAMILIES)
    assert len(additional)==2 and all(number_equal(r['dimK'],32) for r in additional)
    for row in rows+mixed+arrays+additional:
        assert math.isfinite(float(row['area_value'])) and float(row['area_value'])>0
        assert row['area_unit'] in ('','um2','µm²','μm²')
        assert row['source_file'] and int(row['source_row'])>=2
        assert number_equal(row['clk_mhz'],1410)
    assert all(number_equal(r['dimK'],16) for r in rows+mixed)
    assert {r['display_label'] for r in arrays}=={'BF16','FP16','TF32','FP32'}
    for row in rows:
        assert set(row['supported_modes'].split(';'))==set(modes(row['supported_families'].split(';')))
        if row['design_name']=='DotProductBinary':
            assert row['supported_families']=='Binary'


def setup_axis(ax, ylabel):
    ax.set_axisbelow(True)
    ax.grid(axis='y',color='0.91',linewidth=.5)
    ax.set_ylabel(ylabel)
    for side in ('top','right'): ax.spines[side].set_visible(False)
    for side in ('left','bottom'):
        ax.spines[side].set_color('0.4');ax.spines[side].set_linewidth(.7)
    ax.tick_params(width=.6,length=3,pad=3)


def draw(rows,mixed,arrays,additional,gray=False):
    fig=plt.figure(figsize=(14.4,8.8))
    gs=fig.add_gridspec(2,3,left=.112,right=.986,top=.925,bottom=.095,
                        height_ratios=[5.8,1.75],width_ratios=[1.24,.82,1.2],hspace=.44,wspace=.34)
    upper=gs[0,:].subgridspec(2,1,height_ratios=[2.8,2.65],hspace=.045)
    ax=fig.add_subplot(upper[0]);matrix=fig.add_subplot(upper[1],sharex=ax)
    groups={};positions=[];pos=0;previous=None
    for row in rows:
        count=int(row['numeric_mode_count'])
        if previous is not None and count!=previous: pos+=.7
        positions.append(pos);groups.setdefault(count,[]).append(pos)
        pos+=1;previous=count
    lower,upper=-.65,positions[-1]+.65
    values=[float(r['area_value'])/1000 for r in rows]
    ymax=math.ceil(max(values)*1.18/5)*5
    setup_axis(ax,'Unit area (10³ μm²)')
    ax.set(xlim=(lower,upper),ylim=(0,ymax));ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.tick_params(axis='x',bottom=False,labelbottom=False)
    reference=next(float(r['area_value'])/1000 for r in rows if r['precision_set']=='MXFP16BF16FP8FP6FP4')
    ax.axhline(reference,color='0.4' if gray else ACCENT,linestyle=(0,(4,2)),linewidth=.8,zorder=1)
    ax.text(lower+.15,reference+1.4,f'Combined FP (7 modes): {reference:.1f}',fontsize=8,
            color='0.3' if gray else ACCENT,va='bottom')
    for x,row,value in zip(positions,rows,values):
        count=int(row['numeric_mode_count']);highlight=count==9
        edge=('0.15' if gray else ACCENT) if highlight else '0.4'
        hatch='////' if row['lut']=='1' else None
        ax.bar(x,value,width=.69,color='0.77' if gray else COLORS[count],edgecolor=edge,
               linewidth=1.25 if highlight else .65,hatch=hatch,zorder=3)
        ax.text(x,value+1.0,(f'{value:.2f}' if value < 1 else f'{value:.1f}'),ha='center',va='bottom',fontsize=7,
                color=edge,rotation=90,fontweight='bold' if highlight else 'normal')
    for count,xs in groups.items():
        label=f'{count} mode'+('' if count==1 else 's')
        if len(xs)==1: label=label.replace(' ','\n')
        ax.text(sum(xs)/len(xs),1.035,label,transform=ax.get_xaxis_transform(),
                ha='center',va='bottom',fontsize=8,fontweight='bold',linespacing=1.0)
    all_groups=list(groups.values())
    for a,b in zip(all_groups[:-1],all_groups[1:]):
        for panel in (ax,matrix):panel.axvline((a[-1]+b[0])/2,color='0.82',linewidth=.6,linestyle=(0,(2,2)),zorder=0)
    row_labels=list(MODES)+['']+list(EXTRAS)
    for y,label in enumerate(row_labels):
        if label:matrix.hlines(y,lower,upper,color='0.94',linewidth=5,zorder=0)
    for x,row in zip(positions,rows):
        ys=[i for i,label in enumerate(MODES) if label in row['supported_modes'].split(';')]
        matrix.scatter([x]*len(ys),ys,marker='s',s=16,color='0.18' if gray else '#2C6B41',linewidths=0)
        flags=('mx_scaling','nv_scaling','lut','packed_2xfp4')
        ys=[len(MODES)+1+i for i,key in enumerate(flags) if row[key]=='1']
        matrix.scatter([x]*len(ys),ys,marker='D',s=15,color='0.3' if gray else '#477F9A',linewidths=0)
    labels=[r['column_id']+('\nn'+r['norm_kind'] if r['supported_families']=='Binary' else '') for r in rows]
    matrix.set(ylim=(len(row_labels)-.5,-.5),yticks=range(len(row_labels)),
               yticklabels=row_labels,xticks=positions,xticklabels=labels)
    matrix.tick_params(axis='both',length=0,pad=3)
    matrix.tick_params(axis='x',labelsize=7)
    for label in matrix.get_yticklabels():label.set_fontsize(8);label.set_fontweight('bold')
    for spine in matrix.spines.values():spine.set_visible(False)
    matrix.set_xlabel('Measured implementation (one column = one synthesized unit)',fontsize=9,labelpad=6)
    left=fig.add_subplot(gs[1,0]);middle=fig.add_subplot(gs[1,1]);right=fig.add_subplot(gs[1,2])
    for panel,data,title in [(left,mixed,'b  Asymmetric FP × INT · K = 16'),
                             (middle,additional,'c  Additional units · K = 32'),
                             (right,arrays,'d  Outer-product arrays · 8×8, K = 1')]:
        setup_axis(panel,'Area (10³ μm²)')
        vals=[float(r['area_value'])/1000 for r in data]
        panel.bar(range(len(data)),vals,width=.6,color='0.77' if gray else '#AAC5D8',edgecolor='0.4',linewidth=.7,zorder=3)
        panel.set_xticks(range(len(data)),[r['display_label'] for r in data],fontsize=8)
        panel.set_ylim(0,max(vals)*1.22)
        panel.set_title(title,loc='left',fontweight='bold',fontsize=9,pad=10)
        for x,val in enumerate(vals):panel.text(x,val+max(vals)*.035,f'{val:.1f}',ha='center',va='bottom',fontsize=9)
    fig.text(.112,.987,'a  Precision support and measured unit area',ha='left',va='top',fontsize=12,fontweight='bold')
    fig.text(.986,.987,'31 selectable-mode implementations  ·  K = 16  ·  Target clock = 1410 MHz',
             ha='right',va='top',fontsize=9)
    handles=[Patch(facecolor='white',edgecolor='0.4',hatch='////',label='LUT implementation'),
             Patch(facecolor='white',edgecolor='0.2' if gray else ACCENT,linewidth=1.2,label='9-mode combined units'),
             Line2D([0],[0],marker='s',color='none',markerfacecolor='0.18' if gray else '#2C6B41',markeredgewidth=0,label='Numeric mode'),
             Line2D([0],[0],marker='D',color='none',markerfacecolor='0.3' if gray else '#477F9A',markeredgewidth=0,label='Implementation feature')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.56,.005),ncol=4,frameon=False,fontsize=8,handlelength=1.4,columnspacing=2)
    return fig


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--repo-root',type=Path,default=HERE.parents[1])
    parser.add_argument('--output-dir',type=Path,default=HERE)
    args=parser.parse_args();out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    if args.refresh:
        rows,mixed,arrays,additional=refresh(args.repo_root,16,1410)
        for name,data in [('source_data.csv',rows),('mixed_data.csv',mixed),('array_data.csv',arrays),('additional_data.csv',additional)]:write_csv(out/name,data)
    else:
        rows,mixed,arrays,additional=[read_csv(HERE/name) for name in ('source_data.csv','mixed_data.csv','array_data.csv','additional_data.csv')]
        if out.resolve()!=HERE:
            for name,data in [('source_data.csv',rows),('mixed_data.csv',mixed),('array_data.csv',arrays),('additional_data.csv',additional)]:write_csv(out/name,data)
    validate(rows,mixed,arrays,additional)
    units=[{'id':r['column_id'],'precision_set':r['precision_set'],
            'supported_families':r['supported_families'].split(';'),
            'area_um2':float(r['area_value']),'source_file':r['source_file'],
            'source_row':int(r['source_row']),'variant':r['variant'],
            'dimK':16,'clk_mhz':1410} for r in rows]
    (out/'canonical_units.json').write_text(json.dumps(units,indent=2)+'\n')
    previous_path=HERE/'provenance.json'
    previous=json.loads(previous_path.read_text()) if previous_path.exists() else {}
    source_hashes={name:hashlib.sha256((args.repo_root/name).read_bytes()).hexdigest()
                   for name in (FULL,DP) if (args.repo_root/name).is_file()}
    provenance={'source_reference':{'type':'user-supplied repository screenshot','venue':'unspecified','status':'unknown','community':'hardware arithmetic'},
                'target':{'venue':'unspecified','community':'hardware / architecture','placement':'landscape supplemental catalogue'},
                'source_hashes':source_hashes or previous.get('source_hashes',{}),
                'selection':{'main_dimK':16,'clk_mhz':1410,'array_shape':'m8_n8','array_dimK':1,'additional_unit_dimK':32},
                'n_measurements':len(rows),'n_asymmetric_units':len(mixed),'n_arrays':len(arrays),'n_K32_additional':len(additional),
                'area_unit':'um2 (project convention; source area_unit blank)',
                'area_transform':'area_value / 1000; no estimation, summation, or scaling',
                'canonical_selection':'dp_training rows preferred; otherwise explicit midMat selector; aliases deduplicated; no minimum-area selection',
                'physical_size_inches':[14.4,8.8],'intended_placement_width_inches':14.4,
                'minimum_nominal_text_pt':7,'numeric_mode_order':list(MODES),
                'feature_order':list(EXTRAS),'numeric_mode_counts':dict(Counter(r['numeric_mode_count'] for r in rows)),
                'evidence_boundary':'37 released dot-product configuration names:31 canonical K16 units,4 asymmetric K16 units,2 K32-only units; plus4 K1 arrays. No exhaustive integrated RTL subsets. Target clock is not timing closure.',
                'snapshot_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ('source_data.csv','mixed_data.csv','array_data.csv','additional_data.csv')}}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n')
    with plt.rc_context({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,
                         'ps.fonttype':42,'svg.fonttype':'none','axes.labelsize':9,
                         'xtick.labelsize':8,'ytick.labelsize':8,'hatch.linewidth':.45,
                         'savefig.facecolor':'white'}):
        fig=draw(rows,mixed,arrays,additional)
        for suffix in ('png','pdf','svg'):
            target = out / f'{STEM}.{suffix}'
            fig.savefig(target, dpi=220)
            if suffix == 'svg':
                target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines()) + '\n')
        plt.close(fig)
        fig=draw(rows,mixed,arrays,additional,gray=True);fig.savefig(out/f'{STEM}_grayscale.png',dpi=150);plt.close(fig)
    print(f'Rendered {len(rows)} selectable-mode implementations, {len(mixed)} asymmetric units, {len(additional)} K32-only units, {len(arrays)} arrays to {out}')

if __name__=='__main__':main()
