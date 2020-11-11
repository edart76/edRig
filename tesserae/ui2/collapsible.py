""" ref implementation in c++
/*
    Elypson/qt-collapsible-section
*/

#include <QPropertyAnimation>

#include "Section.h"

Section::Section(const QString & title, const int animationDuration, QWidget* parent)
    : QWidget(parent), animationDuration(animationDuration)
{
    toggleButton = new QToolButton(this);
    headerLine = new QFrame(this);
    toggleAnimation = new QParallelAnimationGroup(this);
    contentArea = new QScrollArea(this);
    mainLayout = new QGridLayout(this);

    toggleButton->setStyleSheet("QToolButton {border: none;}");
    toggleButton->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    toggleButton->setArrowType(Qt::ArrowType::RightArrow);
    toggleButton->setText(title);
    toggleButton->setCheckable(true);
    toggleButton->setChecked(false);

    headerLine->setFrameShape(QFrame::HLine);
    headerLine->setFrameShadow(QFrame::Sunken);
    headerLine->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);

    contentArea->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    // start out collapsed
    contentArea->setMaximumHeight(0);
    contentArea->setMinimumHeight(0);

    // let the entire widget grow and shrink with its content
    toggleAnimation->addAnimation(new QPropertyAnimation(this, "minimumHeight"));
    toggleAnimation->addAnimation(new QPropertyAnimation(this, "maximumHeight"));
    toggleAnimation->addAnimation(new QPropertyAnimation(contentArea, "maximumHeight"));

    mainLayout->setVerticalSpacing(0);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    int row = 0;
    mainLayout->addWidget(toggleButton, row, 0, 1, 1, Qt::AlignLeft);
    mainLayout->addWidget(headerLine, row++, 2, 1, 1);
    mainLayout->addWidget(contentArea, row, 0, 1, 3);
    setLayout(mainLayout);

    connect(toggleButton, &QToolButton::toggled, this, &Section::toggle);
}


void Section::toggle(bool collapsed) {
    toggleButton->setArrowType(collapsed ? Qt::ArrowType::DownArrow : Qt::ArrowType::RightArrow);
    toggleAnimation->setDirection(collapsed ? QAbstractAnimation::Forward : QAbstractAnimation::Backward);
    toggleAnimation->start();
}


void Section::setContentLayout(QLayout & contentLayout)
{
    delete contentArea->layout();
    contentArea->setLayout(&contentLayout);
    const auto collapsedHeight = sizeHint().height() - contentArea->maximumHeight();
    auto contentHeight = contentLayout.sizeHint().height();

    for (int i = 0; i < toggleAnimation->animationCount() - 1; ++i)
    {
        QPropertyAnimation* SectionAnimation = static_cast<QPropertyAnimation *>(toggleAnimation->animationAt(i));
        SectionAnimation->setDuration(animationDuration);
        SectionAnimation->setStartValue(collapsedHeight);
        SectionAnimation->setEndValue(collapsedHeight + contentHeight);
    }

    QPropertyAnimation* contentAnimation = static_cast<QPropertyAnimation *>(toggleAnimation->animationAt(toggleAnimation->animationCount() - 1));
    contentAnimation->setDuration(animationDuration);
    contentAnimation->setStartValue(0);
    contentAnimation->setEndValue(contentHeight);
}



"""

from PySide2 import QtWidgets, QtCore, QtGui


delay = 500

class Section(QtWidgets.QWidget):
	""" collapsible widget area """
	def __init__(self, parent=None, title=""):
		super(Section, self).__init__(parent)
		self.button = QtWidgets.QToolButton(self)
		#self.button = QtWidgets.QToolButton(self)
		self.header = QtWidgets.QFrame(self)
		self.toggleAnim = QtCore.QParallelAnimationGroup(self)
		self.contentArea = QtWidgets.QScrollArea(self)
		self.layout = QtWidgets.QGridLayout(self)
		self.isOpen = True

		# self.expandFns = (self.setMinimumHeight, self.setMaximumHeight,
		#                   self.contentArea.setMaximumHeight)

		self.button.setStyleSheet("QToolButton {border: none;}")
		self.button.setToolButtonStyle( QtCore.Qt.ToolButtonTextBesideIcon )
		self.button.setArrowType( QtCore.Qt.ArrowType.RightArrow )
		self.button.setText(title)
		self.button.setCheckable( True )
		#self.button.setChecked( True )

		self.header.setFrameShape( QtWidgets.QFrame.HLine )
		self.header.setSizePolicy( QtWidgets.QSizePolicy.Fixed,
		                               QtWidgets.QSizePolicy.Fixed )

		self.contentArea.setSizePolicy( QtWidgets.QSizePolicy.Expanding,
		                                QtWidgets.QSizePolicy.Expanding )
		self.contentArea.setMaximumHeight(0)
		self.contentArea.setMinimumHeight(0)

		self.layout.setSpacing(0)
		self.layout.setContentsMargins( 0, 0, 0, 0 )

		row = 0
		self.layout.addWidget( self.button, row, 0, 1, 1, QtCore.Qt.AlignLeft )
		self.layout.addWidget( self.header, row + 1, 2, 1, 1 )
		self.layout.addWidget( self.contentArea, row + 1, 0, 1, 3 )
		self.setLayout( self.layout )

		#self.button.triggered.connect( self.toggle )
		self.button.clicked.connect( self.toggle )

	def toggle(self, collapsed=True):
		self.close() if self.isOpen else self.open()


	def open(self):
		self.button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
		self.toggleAnim.setDirection(QtCore.QAbstractAnimation.Forward)
		self.isOpen = True
		contentLayout = self.contentArea.layout()
		collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
		contentHeight = contentLayout.sizeHint().height()

		# for i in range( self.toggleAnim.animationCount()):
		# 	anim = self.toggleAnim.animationAt( i )
		# 	anim.setDuration( delay )
		# 	anim.setStartValue( collapsedHeight )
		# 	anim.setEndValue( collapsedHeight + contentHeight )
		#
		# newAnim = self.toggleAnim.animationAt(
		# 	self.toggleAnim.animationCount() - 1 )
		# newAnim.setDuration( delay )
		# newAnim.setStartValue(0)
		# newAnim.setEndValue(contentHeight)
		# self.toggleAnim.start()

		# for fn in self.expandFns:
		# 	fn(300)
		self.contentArea.setMaximumHeight(10000)


	def close(self):
		self.button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
		self.toggleAnim.setDirection(QtCore.QAbstractAnimation.Backward)
		self.isOpen = False
		contentLayout = self.contentArea.layout()
		collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
		contentHeight = contentLayout.sizeHint().height()

		# print("collapsedHeight {} self sizeHint {}".format(collapsedHeight, self.sizeHint().height()))
		# print("contentAreaMaxHeight {}".format(self.contentArea.maximumHeight()))
		# print("contentHeight {}".format(contentHeight))

		# for i in range( self.toggleAnim.animationCount()):
		# 	anim = self.toggleAnim.animationAt( i )
		# 	anim.setDuration( delay )
		# 	anim.setStartValue( collapsedHeight )
		# 	anim.setEndValue( collapsedHeight + contentHeight )
		#
		# newAnim = self.toggleAnim.animationAt(
		# 	self.toggleAnim.animationCount() - 1 )
		# newAnim.setDuration( delay )
		# newAnim.setStartValue(0)
		# newAnim.setEndValue(contentHeight)
		# self.toggleAnim.start()

		# for fn in self.expandFns:
		# 	fn(50)
		self.contentArea.setMaximumHeight(0)

	def setContentLayout(self, contentLayout):
		""" replaces stored layout with new one
		:type contentLayout : QtWidgets.QLayout """
		self.contentArea.setLayout( contentLayout )
		contentLayout.setSpacing(0)
		contentLayout.setContentsMargins(0, 0, 0, 0)
		# collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
		# contentHeight = contentLayout.sizeHint().height()
		#
		# for i in range( self.toggleAnim.animationCount()):
		# 	anim = self.toggleAnim.animationAt( i )
		# 	anim.setDuration( delay )
		# 	anim.setStartValue( collapsedHeight )
		# 	anim.setEndValue( collapsedHeight + contentHeight )
		#
		# newAnim = self.toggleAnim.animationAt(
		# 	self.toggleAnim.animationCount() - 1 )
		# newAnim.setDuration( delay )
		# newAnim.setStartValue(0)
		# newAnim.setEndValue(contentHeight)
		self.open()


