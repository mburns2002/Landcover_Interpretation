"""slide_font: register the repo-bundled Spectral font and make it the default for presentation figures.

Call use_spectral() after importing matplotlib.pyplot and before creating the figure. The TTFs live in
presentation/assets/fonts/spectral/ so figures render in Spectral without a system font install.
"""

import glob
import os

import matplotlib.pyplot as plt
from matplotlib import font_manager

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts",
                    "spectral")
_registered = False


def use_spectral():
    global _registered
    if not _registered:
        for f in glob.glob(os.path.join(_DIR, "*.ttf")):
            font_manager.fontManager.addfont(f)
        _registered = True
    plt.rcParams["font.family"] = "Spectral"
