import re, os

ICON_PATH = ""
ICON_DOWN_ARROW = os.path.join(ICON_PATH, 'down_arrow.png')

# we reformat the icon file path on windows os.
regex = re.compile('(\w:)')
match = regex.match(ICON_DOWN_ARROW)
if match:
	match_str = match.group(1)
	ICON_DOWN_ARROW = ICON_DOWN_ARROW[len(match_str):]
	ICON_DOWN_ARROW = ICON_DOWN_ARROW.replace('\\', '/')

STYLE_QGROUPBOX = '''
QGroupBox {
	background-color: rgba(0, 0, 0, 0);
	border: 0px solid rgba(0, 0, 0, 0);
	margin-top: 1px;
	padding: 2px;
	padding-top: $PADDING_TOP;
	font-size: 10pt;
}
QGroupBox::title {
	subcontrol-origin: margin;
	subcontrol-position: top center;
	color: rgba(255, 255, 255, 85);
}
'''

STYLE_QLINEEDIT = '''
QLineEdit {
	border: 1px solid rgba(255, 255, 255, 50);
	border-radius: 0px;
	color: rgba(255, 255, 255, 150);
	background: rgba(0, 0, 0, 80);
	selection-background-color: rgba(255, 198, 10, 155);
}
'''

STYLE_TABSEARCH = '''
QLineEdit {
	border: 2px solid rgba(170, 140, 0, 255);
	border-radius: 0px;
	padding: 2px;
	margin: 4px;
	color: rgba(255, 255, 255, 150);
	background: rgba(20, 20, 20, 255);
	selection-background-color: rgba(219, 158, 0, 255);
}
'''


STYLE_TABSEARCH_LIST = '''
QListView {
	background-color: rgba(40, 40, 40, 255);
	border: 1px solid rgba(20, 20, 20, 255);
	color: rgba(255, 255, 255, 150);
	padding-top: 4px;
}
'''

STYLE_QCOMBOBOX = '''
QComboBox {
	border: 1px solid rgba(255, 255, 255, 50);
	border-radius: 0px;
	margin-left: 2px;
	margin-right: 2px;
	margin-top: 1px;
	margin-bottom: 1px;
	padding-left: 4px;
	padding-right: 4px;
}
QComboBox:hover {
	border: 1px solid rgba(255, 255, 255, 80);
}
QComboBox:editable {
	color: rgba(255, 255, 255, 150);
	background: rgba(10, 10, 10, 80);
}
QComboBox:!editable,
QComboBox::drop-down:editable {
	color: rgba(255, 255, 255, 150);
	background: rgba(80, 80, 80, 80);
}
/* QComboBox gets the "on" state when the popup is open */
QComboBox:!editable:on,
QComboBox::drop-down:editable:on {
	background: rgba(150, 150, 150, 150);
}
QComboBox::drop-down {
	background: rgba(80, 80, 80, 80);
	border-left: 1px solid rgba(80, 80, 80, 255);
	width: 20px;
}
QComboBox::down-arrow {
	image: url($ICON_DOWN_ARROW);
}
QComboBox::down-arrow:on {
	/* shift the arrow when popup is open */
	top: 1px;
	left: 1px;
}'''.replace('$ICON_DOWN_ARROW', ICON_DOWN_ARROW)

STYLE_QLISTVIEW = '''
QListView {
	background: rgba(80, 80, 80, 255);
	border: 0px solid rgba(0, 0, 0, 0);
}
QListView::item {
	color: rgba(255, 255, 255, 120);
	background: rgba(60, 60, 60, 255);
	border-bottom: 1px solid rgba(0, 0, 0, 0);
	border-radius: 0px;
	margin: 0px;
	padding: 2px;
}
QListView::item:selected {
	color: rgba(98, 68, 10, 255);
	background: rgba(219, 158, 0, 255);
	border-bottom: 1px solid rgba(255, 255, 255, 5);
	border-radius: 0px;
	margin:0px;
	padding: 2px;
}
'''

STYLE_QMENU = '''
QMenu {
	color: rgba(255, 255, 255, 200);
	background-color: rgba(47, 47, 47, 255);
	border: 1px solid rgba(0, 0, 0, 30);
}

QMenu::item {
	padding: 5px 18px 2px;
	background-color: transparent;
}
QMenu::item:selected {
	color: rgba(98, 68, 10, 255);
	background-color: rgba(219, 158, 0, 255);
}
QMenu::separator {
	height: 1px;
	background: rgba(255, 255, 255, 50);
	margin: 4px 8px;
}
'''

STYLE_QCHECKBOX = '''
QCheckBox {
	color: rgba(255, 255, 255, 150);
	spacing: 8px 2px;
	padding-top: 2px;
	padding-bottom: 2px;
}
QCheckBox::indicator {
	width: 13px;
	height: 13px;
}
'''

# constants



# FILE FORMAT
FILE_IO_EXT = '.ngqt'

# PIPE
PIPE_WIDTH = 3
PIPE_STYLE_DEFAULT = 'line'
PIPE_STYLE_DASHED = 'dashed'
PIPE_STYLE_DOTTED = 'dotted'
PIPE_DEFAULT_COLOR = (127, 149, 151, 255)
PIPE_ACTIVE_COLOR = (70, 255, 220, 255)
PIPE_HIGHLIGHT_COLOR = (232, 184, 13, 255)
PIPE_LAYOUT_STRAIGHT = 0
PIPE_LAYOUT_CURVED = 1

# PORT DEFAULTS
IN_PORT = 'in'
OUT_PORT = 'out'
PORT_ACTIVE_COLOR = (29, 80, 84, 255)
PORT_ACTIVE_BORDER_COLOR = (45, 215, 255, 255)
PORT_HOVER_COLOR = (17, 96, 20, 255)
PORT_HOVER_BORDER_COLOR = (136, 255, 35, 255)


# NODE DEFAULTS
NODE_ICON_SIZE = 24
NODE_SEL_COLOR = (255, 255, 255, 30)
NODE_SEL_BORDER_COLOR = (254, 207, 42, 255)
NODE_MIN_SIZE = (60, 60)

# NODE GRAPH VIEWER DEFAULTS
VIEWER_BG_COLOR = (20, 20, 70, 255)
VIEWER_GRID_COLOR = (100, 100, 100)
VIEWER_GRID_OVERLAY = True

# GRAPH PATHS - sort later
BASE_PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
ICON_PATH = os.path.join(BASE_PATH, 'widgets', 'icons')
ICON_DOWN_ARROW = os.path.join(ICON_PATH, 'down_arrow.png')
ICON_NODE_BASE = os.path.join(ICON_PATH, 'node_base.png')

# DRAW STACK ORDER
Z_VAL_PIPE = -1
Z_VAL_NODE = 1
Z_VAL_PORT = 2
Z_VAL_NODE_WIDGET = 3

