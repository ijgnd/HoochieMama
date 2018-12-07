# -*- coding: utf-8 -*-
# Copyright: (C) 2018 Lovac42
# Support: https://github.com/lovac42/HoochieMama
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.1.4

# Title is in reference to Seinfeld, no relations to the current slang term.

# CONSTANTS:
SHOW_YOUNG_FIRST="order by ivl asc"
SHOW_MATURE_FIRST="order by ivl desc"
SHOW_LOW_REPS_FIRST="order by reps asc"
SHOW_HIGH_REPS_FIRST="order by reps desc"
SORT_BY_OVERDUES="order by due"

# == User Config =========================================

#Prevents round-robin scheduling of forgotten cards.
PRIORITIZE_TODAY = False

#Randomize reviews per subdeck, makes custom_sort randomized by chunks.
IMPOSE_SUBDECK_LIMIT = False

#Default: Reviews are sorted by dues and randomized in chunks.
# CUSTOM_SORT = None
CUSTOM_SORT = SHOW_YOUNG_FIRST
# CUSTOM_SORT = SHOW_MATURE_FIRST
# CUSTOM_SORT = SHOW_LOW_REPS_FIRST
# CUSTOM_SORT = SHOW_HIGH_REPS_FIRST
# CUSTOM_SORT = SORT_BY_OVERDUES

USE_CUSTOM = True
CUSTOM_ASC_CUTOFF = 5

# == End Config ==========================================
##########################################################


import random
import anki.sched
from aqt import mw
from anki.utils import ids2str
from aqt.utils import showText
from anki.hooks import wrap

from anki import version
ANKI21 = version.startswith("2.1.")
on_sync=False


#Turn this on if you are having problems.
def debugInfo(msg):
    # print(msg) #console
    # showText(msg) #Windows
    return


#From: anki.schedv2.py
#Mod:  Various, see logs
def fillRev(self, _old):
    if self._revQueue:
        return True
    if not self.revCount:
        return False
    # Below section is invoked everytime the reviewer is reset (edits, adds, etc)

    # This seem like old comments left behind, and does not affect current versions.
    # Remove these lines for testing
    if self.col.decks.get(self.col.decks.selected(),False)['dyn']:
        # dynamic decks need due order preserved
        return _old(self)


    qc = self.col.conf
    if not qc.get("hoochieMama", False):
        return _old(self)
    debugInfo('using hoochieMama')


    lim=currentRevLimit(self)
    if lim:
        lim=min(self.queueLimit,lim)
        sortBy=CUSTOM_SORT if CUSTOM_SORT else 'order by due'
        if IMPOSE_SUBDECK_LIMIT:
            self._revQueue=getRevQueuePerSubDeck(self,sortBy,lim)
        elif USE_CUSTOM:
            self._revQueue=myqueue(self,sortBy,lim)
        else:
            self._revQueue=getRevQueue(self,sortBy,lim)

        if self._revQueue:
            if CUSTOM_SORT and not IMPOSE_SUBDECK_LIMIT:
                self._revQueue.reverse() #preserve order
            else:
                # fixme: as soon as a card is answered, this is no longer consistent
                r = random.Random()
                # r.seed(self.today) #same seed in case user edits card.
                r.shuffle(self._revQueue)
            return True
    if self.revCount:
        # if we didn't get a card but the count is non-zero,
        # we need to check again for any cards that were
        # removed from the queue but not buried
        self._resetRev()
        return self._fillRev()

    
    
    

def intra_day_randomization_of_revQueue(self, idlist):
    l = []
    for c in idlist:
        #did included only for debugging with print ...
        l.append((c,self.col.getCard(c).ivl,self.col.getCard(c).did))

    same_ListPos= []
    same_IDs = []

    for i in range(len(l)-1):
        same_ListPos.append(i)
        same_IDs.append(l[i])
        if (not l[i][1] == l[i+1][1]) or (i == len(l)-2):
            r = random.Random()
            r.shuffle(same_IDs)
            for i in same_ListPos:
                l[i]=same_IDs.pop() 
            for a,b in enumerate(l):
                idlist[a]=b[0]
            same_ListPos= []
            same_IDs = []
    return idlist


def myqueue(self, sortBy, penetration):
    debugInfo('myqueue')
    deckList=ids2str(self.col.decks.active())

    revQueue = self.col.db.list("""
select id from cards where
did in %s and queue = 2 and due <= ? and ivl < %d
%s limit ?""" % (deckList, CUSTOM_ASC_CUTOFF, sortBy),
                self.today, penetration)

    revQueue = intra_day_randomization_of_revQueue(self,revQueue)

    revQueue.extend(self.col.db.list("""
select id from cards where
did in %s and queue = 2 and due <= ?
%s limit ?""" % (deckList, "order by due"),
                self.today, penetration))

    return revQueue    
    
    

    
    
    
# In the world of blackjack, “penetration”, or “deck penetration”, 
# is the amount of cards that the dealer cuts off, relative to the cards dealt out.
def getRevQueue(self, sortBy, penetration):
    debugInfo('v2 queue builder')
    deckList=ids2str(self.col.decks.active())
    revQueue=[]

    if PRIORITIZE_TODAY:
        revQueue = self.col.db.list("""
select id from cards where
did in %s and queue = 2 and due = ?
%s limit ?""" % (deckList, sortBy),
                self.today, penetration)

    if not revQueue:
        revQueue = self.col.db.list("""
select id from cards where
did in %s and queue = 2 and due <= ?
%s limit ?""" % (deckList, sortBy),
                self.today, penetration)

    return revQueue #Order needs tobe reversed for custom sorts



def getRevQueuePerSubDeck(self,sortBy,penetration):
    debugInfo('per subdeck queue builder')
    revQueue=[]
    pen=penetration//len(self.col.decks.active())
    pen=max(5,pen) #if div by large val
    for did in self.col.decks.active():
        d=self.col.decks.get(did)
        lim=deckRevLimitSingle(self,d,pen)
        if not lim: continue

        arr=None
        if PRIORITIZE_TODAY:
            arr=self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due = ?
%s limit ?"""%sortBy, did, self.today, lim)

        if not arr:
            arr=self.col.db.list("""
select id from cards where
did = ? and queue = 2 and due <= ?
%s limit ?"""%sortBy, did, self.today, lim)

        revQueue.extend(arr) 
        if len(revQueue)>=penetration: break
    return revQueue #randomized later



#From: anki.schedv2.py
def currentRevLimit(self):
    d = self.col.decks.get(self.col.decks.selected(), default=False)
    return deckRevLimitSingle(self, d)


#From: anki.schedv2.py
def deckRevLimitSingle(self, d, parentLimit=None):
    if not d: return 0  # invalid deck selected?
    if d['dyn']: return 99999

    c = self.col.decks.confForDid(d['id'])
    lim = max(0, c['rev']['perDay'] - d['revToday'][1])
    if parentLimit is not None:
        return min(parentLimit, lim)
    elif '::' not in d['name']:
        return lim
    else:
        for parent in self.col.decks.parents(d['id']):
            # pass in dummy parentLimit so we don't do parent lookup again
            lim = min(lim, deckRevLimitSingle(self, parent, parentLimit=lim))
        return lim




#For reviewer count display (cosmetic)
def resetRevCount(self, _old):
    if on_sync:
        return _old(self)

    qc = self.col.conf
    if not qc.get("hoochieMama", False):
        return _old(self)

    if IMPOSE_SUBDECK_LIMIT:
        return _resetRevCountV1(self)
    return _resetRevCountV2(self)


#From: anki.schedv2.py
def _resetRevCountV2(self):
    lim = currentRevLimit(self)
    self.revCount = self.col.db.scalar("""
select count() from (select id from cards where
did in %s and queue = 2 and due <= ? limit %d)""" % (
        ids2str(self.col.decks.active()), lim), self.today)

#From: anki.sched.py
def _resetRevCountV1(self):
    def _deckRevLimitSingle(d):
        if not d: return 0
        if d['dyn']: return 1000
        c = mw.col.decks.confForDid(d['id'])
        return max(0, c['rev']['perDay'] - d['revToday'][1])
    def cntFn(did, lim):
        return self.col.db.scalar("""
select count() from (select id from cards where
did = ? and queue = 2 and due <= ? limit %d)""" % lim,
                                      did, self.today)
    self.revCount = self._walkingCount(
        _deckRevLimitSingle, cntFn)



anki.sched.Scheduler._fillRev = wrap(anki.sched.Scheduler._fillRev, fillRev, 'around')
anki.sched.Scheduler._resetRevCount = wrap(anki.sched.Scheduler._resetRevCount, resetRevCount, 'around')
if ANKI21:
    import anki.schedv2
    anki.schedv2.Scheduler._fillRev = wrap(anki.schedv2.Scheduler._fillRev, fillRev, 'around')
    anki.schedv2.Scheduler._resetRevCount = wrap(anki.schedv2.Scheduler._resetRevCount, resetRevCount, 'around')



#This monitor sync start/stops
oldSync=anki.sync.Syncer.sync
def onSync(self):
    global on_sync
    on_sync=True
    ret=oldSync(self)
    on_sync=False
    return ret

anki.sync.Syncer.sync=onSync



##################################################
#
#  GUI stuff, adds preference menu options
#
#################################################
import aqt
import aqt.preferences
from aqt.qt import *


if ANKI21:
    from PyQt5 import QtCore, QtGui, QtWidgets
else:
    from PyQt4 import QtCore, QtGui as QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

def setupUi(self, Preferences):
    r=self.gridLayout_4.rowCount()
    self.hoochieMama = QtWidgets.QCheckBox(self.tab_1)
    self.hoochieMama.setObjectName(_fromUtf8("hoochieMama"))
    self.hoochieMama.setText(_('Hoochie Mama! Randomize Queue'))
    self.hoochieMama.toggled.connect(lambda:toggle(self))
    self.gridLayout_4.addWidget(self.hoochieMama, r, 0, 1, 3)

def __init__(self, mw):
    qc = self.mw.col.conf
    cb=qc.get("hoochieMama", 0)
    self.form.hoochieMama.setCheckState(cb)

def accept(self):
    qc = self.mw.col.conf
    qc['hoochieMama']=self.form.hoochieMama.checkState()

def toggle(self):
    checked=not self.hoochieMama.checkState()==0
    if checked:
        try:
            self.serenityNow.setCheckState(0)
        except: pass

aqt.forms.preferences.Ui_Preferences.setupUi = wrap(aqt.forms.preferences.Ui_Preferences.setupUi, setupUi, "after")
aqt.preferences.Preferences.__init__ = wrap(aqt.preferences.Preferences.__init__, __init__, "after")
aqt.preferences.Preferences.accept = wrap(aqt.preferences.Preferences.accept, accept, "before")
