#! /usr/bin/env python

"""
Author: Lori Garzio on 2/14/2025
Last modified: 2/14/2025
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import make_axes_locatable
plt.rcParams.update({'font.size': 12})


def xsection(fig, ax, x, y, z, xlabel='Time', ylabel='Depth (m)', clabel=None, cmap='jet', title=None, date_fmt=None,
             grid=None, extend='both'):
    xc = ax.scatter(x, y, c=z, cmap=cmap, s=10, edgecolor='None')

    ax.invert_yaxis()
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)

    if title:
        ax.set_title(title, fontsize=16)

    # format colorbar
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)
    if clabel:
        cb = plt.colorbar(xc, cax=cax, label=clabel, extend=extend)
    else:
        cb = plt.colorbar(xc, cax=cax, extend=extend)

    # format x-axis
    if date_fmt:
        xfmt = mdates.DateFormatter(date_fmt)
        ax.xaxis.set_major_formatter(xfmt)

    if grid:
        ax.grid(ls='--', lw=.5)
