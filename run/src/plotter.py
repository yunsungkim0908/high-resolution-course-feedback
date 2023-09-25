import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from scipy import stats
from src.utils import (
    get_final_survey_week_number,
    week_string
)

def plot_mood(class_hash, analyzer, answers, predictor):
    sampled_weeks = predictor.weeks # weeks that have responses

    # week_of_query = analyzer.week_of_query[class_hash]
    # first_survey_week = analyzer.classes_info[class_hash]['first_survey_week']

    # all_rel_weeks = range(first_survey_week,week_of_query+1)
    # all_abs_weeks = [
    #     week_string(
    #         analyzer.global_date,
    #         offset=(i-week_of_query)
    #     ) for i in all_rel_weeks
    # ]

    final_week = get_final_survey_week_number(analyzer.classes_info[class_hash])
    call_number = analyzer.classes_info[class_hash]['callNumber']
    # groups_stats = analyzer.groups_stats

    posterior_samples = [
        get_samples(
            predictor.mu[i],
            predictor.var[i],
            5000)
        for i in range(len(sampled_weeks))
    ]
    labels = []
    fig, ax = plt.subplots(figsize=(12,6))
    ax.set_title(f'[{call_number}] Estimated Mood of Your Class')
    ax.set_xlim(1,final_week+1)
    ax.set_xticks(list(range(2, final_week+1)))
    violin, avg, whisker = violinplot(
        posterior_samples, predictor.mu,
        predictor.var, sampled_weeks
    )

    # group mood average plots

    # for grp in ['all', analyzer.class_to_group[class_hash]]:
    #     print(class_hash, call_number, grp)
    #     if grp is None:
    #         print(f'{class_hash} not found in group info')
    #         continue

    #     if groups_stats[analyzer.global_week][grp] is None:
    #         print(f'{class_hash}\'s group "{grp}" is omitted in group stats')
    #         continue

    #     color = 'gold' if grp == 'all' else 'pink'
    #     valid_grp_idx = [
    #         i for i, abs_week in enumerate(all_abs_weeks)
    #         if groups_stats[abs_week][grp] is not None
    #     ]

    #     valid_grp_weeks = [all_rel_weeks[i] for i in valid_grp_idx]
    #     valid_grp_abs_weeks = [all_abs_weeks[i] for i in valid_grp_idx]

    #     print(valid_grp_weeks)
    #     print([groups_stats[week][grp]['avg'] for week in valid_grp_abs_weeks])
    #     grp_avg, = ax.plot(
    #         valid_grp_weeks,
    #         [groups_stats[week][grp]['avg'] for week in valid_grp_abs_weeks],
    #         marker=('o' if len(valid_grp_weeks)==1 else None),
    #         color=color
    #     )
    #     ax.fill_between(
    #         valid_grp_weeks,
    #         [groups_stats[week][grp]['avg_low'] for week in valid_grp_abs_weeks],
    #         [groups_stats[week][grp]['avg_high'] for week in valid_grp_abs_weeks],
    #         color=color, alpha=0.5
    #     )

    #     labels.append((grp_avg, f'Average Mood across {grp.title()} Classes'))

    color = violin['bodies'][0].get_facecolor().flatten()
    labels.append((mpatches.Patch(color=color), 'Uncertainty Region'))
    labels.append((whisker, '+/-1 Std'))
    labels.append((avg, 'Average Mood'))

    ax.legend(*zip(*labels))
    return fig

def plot_rating(title, answers, xtick_labels):
    average = np.mean(answers)
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_title(title)
    ax.hist(answers)
    ratings = np.arange(1,6)
    freq = np.bincount(answers, minlength=6)[1:]
    scaleY = 1/len(answers)
    ax.bar(ratings, freq)

    y0, y1 = ax.get_ybound()
    axTwinY = ax.twinx()

    if ax.get_aspect() in ['equal',1.,1]:
        axTwinY.set_aspect(1./scaleY)
    axTwinY.set_ybound(y0*scaleY, y1*scaleY)
    axTwinY.set_ylabel('Fraction')
    ax.set_ylabel('Frequency')
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(xtick_labels)
    ax.axvline(x=average, color='r', label=f'week average ({average:.2f})\n({len(answers)} responses)')
    ax.legend(loc='upper left')

    return fig

def adjacent_values(vals, q1, q3):
    upper_adjacent_value = q3 + (q3 - q1) * 1.5
    upper_adjacent_value = np.clip(upper_adjacent_value, q3, vals[-1])

    lower_adjacent_value = q1 - (q3 - q1) * 1.5
    lower_adjacent_value = np.clip(lower_adjacent_value, vals[0], q1)
    return lower_adjacent_value, upper_adjacent_value

def violinplot(data, mu, var, weeks, ax=None):
    ax = plt if ax is None else ax
    ax.ylabel('Class Mood')
    ax.xlabel('Week')
    violin = ax.violinplot(data, positions=weeks, showmedians=False,
                  showextrema=False, showmeans=False)

    mu = np.array(mu)+3
    std = np.sqrt(np.array(var))
    inds = weeks[:len(data)]
    avg, = ax.plot(inds, mu, 'ro-',
                   markersize=5, zorder=3, label='Average Mood')
    whisker = ax.vlines(inds, mu-std, mu+std,
                        color='grey', linestyle='-', lw=5, label='+/-1 STD')
    return violin, avg, whisker

def get_samples(mu, var, n):
    return stats.norm.rvs(loc=mu+3, scale=np.sqrt(var), size=n)

