from system.scheduler import scheduler
from system.hexpansion.app import HexpansionManagerApp
from system.patterndisplay.app import PatternDisplay
from system.backleds.app import BackLEDManager
from system.notification.app import NotificationService
from system.espnow import espnow_service
from system.launcher.app import Launcher
from system.power.handler import PowerEventHandler
from system.power.app import PowerManager
from system.boopscreen.app import BoopSpinner

from frontboards.twentysix import TwentyTwentySix
from frontboards.twentyfour import TwentyTwentyFour


def killOtherStuff():
    scheduler.stop_app(TwentyTwentySix())
    scheduler.stop_app(TwentyTwentyFour())
    scheduler.stop_app(HexpansionManagerApp())
    scheduler.stop_app(BoopSpinner())
    scheduler.stop_app(PatternDisplay())
    scheduler.stop_app(BackLEDManager())
    scheduler.stop_app(Launcher())
    scheduler.stop_app(NotificationService())
    scheduler.stop_app(PowerManager())

    print("NOTICE: Stopped other apps to make way for MusicJam")
