# -*- coding: utf-8 -*-

import os
import pkg_resources

try:
    from PIL import Image
    from pybot.minitel.image import VideotexImage
except ImportError:
    Image = VideotexImage = None

from pybot.minitel import Minitel, DeviceCommunicationError, constants
from pybot.minitel.menu import Menu

from pybot.youpi2.app import YoupiApplication, ApplicationError
from pybot.youpi2.model import YoupiArm, OutOfBoundError

from __version__ import version

__author__ = 'Eric Pascual'

__all__ = ['MinitelUIApp', 'main']

_my_package = '.'.join(__name__.split('.')[:-1])


class action(object):
    """ Decorator used to register methods implementing  an action
    which can be started from the menu.
    """

    def __init__(self, actions, label=None):
        self.actions = actions
        self.label = label

    def __call__(self, func, *args, **kwargs):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        label = self.label or func.__doc__ or func.__name__
        # print('adding action "%s"' % label)
        self.actions.append((label, func))

        return wrapper


class MinitelUIApp(YoupiApplication):
    """ This application implements a Videotex server for managing
    a user interfaced based on a Minitel.
    """

    NAME = 'minitel'
    TITLE = "Minitel UI"
    VERSION = version

    DEFAULT_MINITEL_DEVICE = "/dev/ttyUSB0"

    _mt = None
    _exit_allowed = False
    _actions = []

    def add_custom_arguments(self, parser):
        parser.add_argument('--minitel-device', default=self.DEFAULT_MINITEL_DEVICE)
        parser.add_argument('--exit-allowed', action='store_true', default=False)

    def setup(self, minitel_device=DEFAULT_MINITEL_DEVICE, exit_allowed=False, **kwargs):
        if not os.path.exists(minitel_device):
            raise ValueError('device not found : %s' % minitel_device)

        self.log_info('initializing Minitel proxy (device=%s)', minitel_device)
        self._mt = Minitel(minitel_device)

        self._exit_allowed = exit_allowed

        self._mt.clear_all()
        self._mt.display_status(
            self._mt.text_style_sequence(inverse=True) +
            u'Démonstration YouPinitel'.ljust(self._mt.get_screen_width())
        )

    def on_terminate(self, *args):
        self.log_info('interrupting ongoing read')
        self._mt.interrupt()

    def teardown(self, exit_code):
        self._mt.clear_all()
        self._mt.display_text(u"I'll be back...")

        if Image:
            img_path = pkg_resources.resource_filename(_my_package, 'data/img/pobot-logo-small.png')
            img = Image.open(img_path)
            vt_img = VideotexImage(img)
            code = vt_img.to_videotex()

            self._mt.videotex_graphic_mode()
            self._mt.send(code)
        else:
            self.log_warning('PIL not installed. Unable to display graphics.')

        self._mt.shutdown()

    _trans = {ord(f): t for f, t in zip(u'àâäéèëêïîöôùüûç', u'aaaeeeeiioouuuc')}

    def display_text(self, s, line=3, centered=True):
        if centered:
            self.pnl.center_text_at(s.translate(self._trans)[:20], line=line)
        else:
            self.pnl.write_at(s.translate(self._trans)[:20], line=line, col=1)

    def loop(self):
        if not self._actions:
            raise ApplicationError('actions list as not been initialized by decorators')

        title = 'Menu principal'

        addit = [(0, 23, ' SOMMAIRE: fin '.center(40, '-'))] if self._exit_allowed else []
        while True:
            msg = u'displaying main menu'
            self.log_info(msg)
            self.display_text(msg)

            menu = Menu(
                self._mt,
                title=[title, '-' * len(title)],
                choices=[t[0] for t in self._actions],
                prompt='Votre choix',
                line_skip=2,
                margin_top=1,
                prompt_line=20,
                addit=addit,
                cancelable=self._exit_allowed
            )

            try:
                choice = menu.get_choice()

                self.log_info('selected choice : %s', choice)
                if self.terminated:
                    return True

                if not choice:
                    if self._exit_allowed:
                        return True
                    else:
                        continue

                label, method = self._actions[choice - 1]

                self.log_info('invoking action : %s', label)
                self.display_text(label)

                method(self)

                if self.terminated:
                    return True

            except DeviceCommunicationError as e:
                if 'Interrupted system call' in str(e):   # we got an interruption signal from the outside
                    self.log_info('system call interrupted by external signal')
                    return True
                else:
                    self.log_error_banner(e, unexpected=True)
                    self.log_exception(e)

    @action(_actions)
    def display_infos(self):
        u"""quelques explications"""

        self._mt.clear_screen()
        for l, text in enumerate([
            u'La rencontre des années 80:',
            u'',
            u"Youpi: ",
            u"   Un bras robotique pour l'enseignement",
            "",
            u"Le Minitel: ",
            u"   L'ancêtre d'Internet",
            u'',
            u'... et du 21ème siècle:',
            u'',
            u"La RaspberryPi: ",
            u"   Un ordinateur de la taille d'une ",
            u"   carte de crédit"
        ]):
            self._mt.display_text(text=text, x=0, y=l + 2)

        self._mt.display_text_center(u'Retour : menu principal', y=23)
        self._mt.wait_for_key([constants.SEP + constants.KeyCode.RETOUR], max_wait=300)

    # def simple_gesture(self):
    #     u"""dis bonjour avec le bras"""
    #     self._mt.display_text_center(' je vous dis bonjour ', 23, pad_char='-')
    #     pose_extended = {
    #         "shoulder": 170,  # 82,
    #         "elbow": 60,  # 73,
    #         "base": 240,
    #         "wrist": 202,
    #         "gripper": 150
    #     }
    #     pose_to_the_right = {
    #         "base": 200
    #     }
    #     pose_to_the_left = {
    #         "base": 280
    #     }
    #
    #     gesture = Gesture([
    #         (pose_extended, 1),
    #         (None, 0.5),
    #         (pose_to_the_right, 0.5),
    #         (pose_to_the_left, 1),
    #         (pose_extended, 0.5),
    #         (None, 1),
    #         (self.pose_home, 2)
    #     ])
    #     data = gesture.as_json() if self._arm_busname else gesture
    #     self._arm.execute_gesture(data)

    @action(_actions)
    def manual_control(self):
        u"""contrôle manuel"""
        INFO_MSG_LINE = 18

        def info_message(s):
            self._mt.display_text_center(s, y=INFO_MSG_LINE)

        def info_clear():
            self._mt.goto_xy(0, INFO_MSG_LINE)
            self._mt.clear_line()

        def info_ready():
            info_message(u'Prêt')

        def _move_joint(joint, angle):
            self.log_info('moving joint %s %5.1f degrees', joint, angle)
            self.arm.move({joint: angle}, True)

        def shoulder_up():
            _move_joint(YoupiArm.MOTOR_SHOULDER, 5)

        def shoulder_down():
            _move_joint(YoupiArm.MOTOR_SHOULDER, -5)

        def elbow_up():
            _move_joint(YoupiArm.MOTOR_ELBOW, 5)

        def elbow_down():
            _move_joint(YoupiArm.MOTOR_ELBOW, -5)

        def wrist_up():
            _move_joint(YoupiArm.MOTOR_WRIST, +5)

        def wrist_down():
            _move_joint(YoupiArm.MOTOR_WRIST, -5)

        def base_left():
            _move_joint(YoupiArm.MOTOR_BASE, 5)

        def base_right():
            _move_joint(YoupiArm.MOTOR_BASE, -5)

        def gripper_open():
            self.arm.open_gripper(True)

        def gripper_close():
            self.arm.close_gripper(True)

        def wrist_ccw():
            _move_joint(YoupiArm.MOTOR_HAND_ROT, -5)

        def wrist_cw():
            _move_joint(YoupiArm.MOTOR_HAND_ROT, 5)

        def go_home():
            self.arm.go_home([m for m in YoupiArm.MOTORS_ALL if m != YoupiArm.MOTOR_GRIPPER], True)

        actions = {
            '1': shoulder_up,
            '4': shoulder_down,
            '2': elbow_up,
            '5': elbow_down,
            '3': wrist_up,
            '6': wrist_down,
            '7': base_left,
            '9': base_right,
            'O': gripper_open,
            'F': gripper_close,
            '*': wrist_ccw,
            '#': wrist_cw,
            'R': go_home,
        }

        self._mt.clear_screen()
        for l, text in enumerate([
            u'Utilisez les touches du clavier',
            u'pour contrôler le bras.',
            '',
            u'1 4 : épaule',
            u'2 5 : coude',
            u'3 6 : poignet',
            u'7 9 : rotation bras',
            u'* # : rotation pince',
            u'O F : ouverture/fermeture pince',
            '',
            u' R  : retour position initiale'
        ]):
            self._mt.display_text(text=text, x=0, y=l + 4)

        self._mt.display_text_center(u'Retour : menu principal', y=23)

        key_return = constants.SEP + constants.KeyCode.RETOUR
        valid_keys = actions.keys() + [key_return]

        hline = '-' * self._mt.get_screen_width()
        self._mt.display_text(hline, y=INFO_MSG_LINE - 1)
        self._mt.display_text(hline, y=INFO_MSG_LINE + 1)

        info_ready()

        while True:
            key = self._mt.wait_for_key(valid_keys, max_wait=60)
            if key in (None, key_return):
                if not key:
                    self.log_info('no input => return to main menu')
                self._mt.clear_screen()
                self._mt.display_text_center(u"Réinitialisation du bras", y=5)
                self._mt.display_text_center(u"Veuillez patienter...", y=7)
                self.arm.go_home([m for m in YoupiArm.MOTORS_ALL if m != YoupiArm.MOTOR_GRIPPER], True)
                return

            else:
                info_clear()
                try:
                    action_func = actions[key]
                except KeyError:
                    self._mt.beep()
                    info_message(u'Touche incorrecte')
                else:
                    try:
                        info_message(u'Mouvement en cours. Patientez...')
                        action_func()
                    except OutOfBoundError as e:
                        self._mt.beep()
                        info_message(u'Limite mécanique atteinte')
                    else:
                        info_ready()


def main():
    MinitelUIApp().main()
