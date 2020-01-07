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
		self.button = QtWidgets.QToolButton(parent=self)
		self.header = QtWidgets.QFrame(parent=self)
		self.toggleAnim = QtCore.QParallelAnimationGroup(parent=self)
		self.contentArea = QtWidgets.QScrollArea(parent=self)
		self.layout = QtWidgets.QGridLayout(parent=self)

		self.button.setStyleSheet("QToolButton {border: none;}")
		self.button.setToolButtonStyle( QtCore.Qt.ToolButtonTextBesideIcon )
		self.button.setArrowType( QtCore.Qt.ArrowType.RightArrow )
		self.button.setText(title)
		self.button.setCheckable( True )
		self.button.setChecked( True )

		self.headerLine.setFrameShape( QtWidgets.QFrame.HLine )
		self.headerLine.setSizePolicy( QtWidgets.QSizePolicy.Expanding,
		                               QtWidgets.QSizePolicy.Maximum )

		self.contentArea.setSizePolicy( QtWidgets.QSizePolicy.Expanding,
		                                QtWidgets.QSizePolicy.Fixed )
		self.contentArea.setMaximumHeight(0)
		self.contentArea.setMinimumHeight(0)

		self.toggleAnim.addAnimation( QtCore.QPropertyAnimation(
			parent=self, propertyName="minimumHeight" ) )
		self.toggleAnim.addAnimation( QtCore.QPropertyAnimation(
			parent=self, propertyName="maximumHeight" ) )
		self.toggleAnim.addAnimation( QtCore.QPropertyAnimation(
			parent=self.contentArea, propertyName="maximumHeight" ) )

		self.layout.setVerticalSpacing(0)
		self.layout.setContentsMargins( 0, 0, 0, 0 )

		row = 0
		self.layout.addWidget( self.button, row, 0, 1, 1, QtCore.Qt.AlignLeft )
		self.layout.addWidget( self.header, row + 1, 2, 1, 1 )
		self.layout.addWidget( self.contentArea, row + 1, 0, 1, 3 )
		self.setLayout( self.layout )

		self.button.triggered.connect( self.toggle )

	def toggle(self, collapsed=True):
		self.button.setArrowType( QtCore.Qt.ArrowType.DownArrow if collapsed else
		                          QtCore.Qt.ArrowType.RightArrow )
		self.toggleAnim.setDirection( QtCore.QAbstractAnimation.Forward if collapsed else
		                              QtCore.QAbstractAnimation.Backward)
		self.toggleAnim.start()

	def setContentLayout(self, contentLayout):
		""" replaces stored layout with new one
		:type contentLayout : QtWidgets.QLayout """
		self.contentArea.setLayout( contentLayout )
		collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
		contentHeight = contentLayout.sizeHint().height()

		for i in range( self.toggleAnim.animationCount()):
			anim = self.toggleAnim.animationAt( i )
			anim.setDuration( delay )
			anim.setStartValue( collapsedHeight )
			anim.setEndValue( collapsedHeight + contentHeight )

		newAnim = self.toggleAnim.animationAt(
			self.toggleAnim.animationCount() - 1 )
		newAnim.setDuration( delay )
		newAnim.setStartValue(0)
		newAnim.setEndValue(contentHeight)


