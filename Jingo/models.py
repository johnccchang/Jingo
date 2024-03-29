from __future__ import unicode_literals
import base64
import datetime
import string
from math import radians, cos, sin, asin, sqrt

#from django.utils import timezone
from django.db import models
from Jingo.lib.config import *
from Jingo.lib.SQLExecution import SQLExecuter
from Jingo.lib.DataVerification import JingoTimezone

class Log_Keywords(models.Model, HttpRequestResponser, Formatter):
    logid   = models.IntegerField(primary_key=True)
    uid     = models.ForeignKey('User', db_column='uid')
    keyword = models.CharField(max_length=60)
    k_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    k_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    k_timestamp = models.DateTimeField()
    
    class Meta:
        db_table = 'log_keywords'

    def getNewLogid(self):
        if len(Log_Keywords.objects.all().values()) == 0:
            return 1
        else:
            log = Log_Keywords.objects.all().order_by('logid').latest('logid')
            return log.logid + 1
        
    def logUserKeywords(self, data, keywords):
        #currenttime         = timezone.now()
        currenttime         = JingoTimezone().getLocalTime()
        data['u_longitude'] = "%.6f" % float(data['u_longitude'])
        data['u_latitude']  = "%.6f" % float(data['u_latitude'])
        for keyword in keywords:
            values = [self.getNewLogid(), int(data['uid']), keyword, data['u_longitude'], data['u_latitude'], currenttime]
            args   = dict([('table', 'log_keywords'), ('values', values)])
            SQLExecuter().doInsertData(args)

class Friend(models.Model, HttpRequestResponser, Formatter):
    uid = models.ForeignKey('User', db_column='uid')
    f_uid = models.ForeignKey('User', db_column='f_uid')
    is_friendship = models.IntegerField()
    invitationid = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'friend'

    def getNewInvitationid(self):
        if len(Friend.objects.all().values()) == 0:
            return 1
        else:
            friend = Friend.objects.all().order_by('invitationid').latest('invitationid')
            return friend.invitationid + 1

    def getFriendsInvitations(self, input_uid):
        return Friend.objects.filter(uid=input_uid, is_friendship=2).order_by('invitationid').values()

    def getFriendsList(self, data):
        alist = list(Friend.objects.filter(uid=data['uid'], is_friendship=1).order_by('invitationid').values_list('f_uid', flat=True))
        blist = list(Friend.objects.filter(f_uid=data['uid'], is_friendship=1).order_by('invitationid').values_list('uid', flat=True))
        return alist + blist

    def addInvitation(self, data):
        newInvitationid = self.getNewInvitationid()
        # 0:denied, 1:accepted, 2:pending, 3:cancel
        values          = [int(data['uid']), int(data['f_uid']), 2, newInvitationid]
        args            = dict([('table', 'friend'), ('values', values)])
        SQLExecuter().doInsertData(args)
        
        data['friendship']   = 'pending'
        data['invitationid'] = newInvitationid
        
        return data

    def responseInvitation(self, data):
        Friend.objects.filter(invitationid=data['invitationid']).update(is_friendship=data['reply'])
        data['friendship'] = data['reply']
        return data
    
    def getFriendsInfoList(self, data):
        flist = []
        alist = Friend.objects.filter(uid=data['uid'],is_friendship=1).values()
        blist = Friend.objects.filter(f_uid=data['uid'],is_friendship=1).values()
        for friend in alist:
            fuser                 = User.objects.filter(uid=friend['f_uid_id']).values()[0]
            fuser['invitationid'] = friend['invitationid']
            flist.append(fuser)
        
        for friend in blist:
            fuser                 = User.objects.filter(uid=friend['uid_id']).values()[0]
            fuser['invitationid'] = friend['invitationid']
            flist.append(fuser)
            
        return flist
    
    def getPendingsInfoList(self, data):
        strSQL = 'Select uid, invitationid From friend Where is_friendship = 2 And f_uid= %s And uid Not In (Select f_uid From friend Where is_friendship = 1 And uid = %s)'
        args   = [data['uid'], data['uid']]
        plist  = SQLExecuter().doRawSQL(strSQL, args)
        flist  = []
        for friend in plist:
            fuser                 = User.objects.filter(uid=friend['uid']).values()[0]
            fuser['invitationid'] = friend['invitationid']
            flist.append(fuser)
        return flist
    
    def checkFriendship(self, reader, poster):
        #print reader
        #print poster
        alist = Friend.objects.filter(uid=reader, f_uid=poster)
        blist = Friend.objects.filter(uid=poster, f_uid=reader)
        #print alist.values()
        #print blist.values()
        n_alist = len(alist)
        n_blist = len(blist)
        
        #print "n_alist=" + str(n_alist) + ", nblist=" + str(n_blist)
        #print "friend_status"
        if n_alist == 0 and n_blist > 0: 
            blist = blist.order_by('invitationid').latest('invitationid')
            #print "blist"
            #print blist
            #print blist.is_friendship
            return blist.is_friendship
            
        if n_blist == 0 and n_alist > 0:
            alist = alist.order_by('invitationid').latest('invitationid')
            #print "alist"
            #print alist
            #print alist.is_friendship
            return alist.is_friendship
        
        if n_alist > 0 and n_blist > 0:
            alist = alist.order_by('invitationid').latest('invitationid')
            blist = blist.order_by('invitationid').latest('invitationid')
            if int(alist.invitationid) > int(blist.invitationid):
                return alist.is_friendship
            else:
                return blist.is_friendship
        return 0

    def cancelFriendship(self, data):
        Friend.objects.filter(uid=data['uid'], f_uid=data['f_uid'], is_friendship__in=[1,2]).update(is_friendship=3)
        Friend.objects.filter(uid=data['f_uid'], f_uid=data['uid'], is_friendship__in=[1,2]).update(is_friendship=3)
        return data
        
class Comments(models.Model, HttpRequestResponser, Formatter):
    commentid = models.IntegerField(primary_key=True)
    noteid = models.ForeignKey('Note', db_column='noteid')
    c_timestamp = models.DateTimeField()
    uid = models.ForeignKey('User', db_column='uid')
    c_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    c_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    comment = models.CharField(max_length=140)

    class Meta:
        db_table = 'comments'

    def getNewCommentid(self):
        if len(Comments.objects.all().values()) == 0:
            return 1
        else:
            nComments = Comments.objects.all().order_by('commentid').latest('commentid')
            return nComments.commentid + 1

    def addComment(self, data):
        newCommentid = self.getNewCommentid()
        data['c_longitude'] = "%.6f" % float(data['c_longitude'])
        data['c_latitude'] = "%.6f" % float(data['c_latitude'])
        values = [newCommentid, int(data['noteid']), JingoTimezone().getLocalTime(), int(data['uid']), float(data['c_latitude']),
                  float(data['c_longitude']), data['comment']]
        #print values
        args = dict([('table', 'comments'), ('values', values)])
        SQLExecuter().doInsertData(args)
        return newCommentid

    def retrieveComments(self, data):
        result = []
        for comm in Comments.objects.filter(noteid=data['noteid']).values():
            replier = User.objects.filter(uid=comm['uid_id']).values('u_name')[0]['u_name']
            comm['replier'] = replier
            result.append(comm)
        return result

class Filter(models.Model, HttpRequestResponser, Formatter):
    stateid      = models.ForeignKey('State', db_column='stateid', primary_key=True)
    tagid        = models.ForeignKey('Tag', db_column='tagid', primary_key=True)
    f_start_time = models.DateTimeField(null=True, blank=True)
    f_stop_time  = models.DateTimeField(null=True, blank=True)
    f_repeat     = models.IntegerField(null=True, blank=True)
    f_visibility = models.IntegerField()
    uid          = models.ForeignKey('State', db_column='uid', primary_key=True)
    is_checked   = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'filter'

    def categorizeFiltersIntoSystags(self, data, filterset):
        result, sysTags = [[], {}]
        
        # get default system tags
        for sys in Tag().getSysTags('include'):
            sys['tags']           = []
            sys['is_checked']     = 0
            sysTags[sys['tagid']] = sys
        
        # categorize each filter into the right system tag as a child tag
        for row in filterset:
            tagid     = row['tagid_id']
            sys_tagid = row['sys_tagid'] 
            
            # this is a system tag
            if tagid >= 0 and tagid <= 10:
                sysTags[tagid]['is_checked'] = row['is_checked']
                
            # this is a child tag
            if tagid > 10:
                sysTags[sys_tagid]['is_checked'] = row['is_checked']
                sysTags[sys_tagid]['tags'].append(row)
        
        for sys in sysTags:
            result.append(sysTags[sys])
        
        return result

    def extendFilterWithTagInfo(self, data, filterset):
        result = []
        for row in filterset:
            tagid_id         = row['tagid_id']
            tag              = Tag.objects.get(tagid=tagid_id)
            row['tag_name']  = tag.tag_name
            row['sys_tagid'] = tag.sys_tagid
            result.append(row)
        return result

    def getUserStateFilters(self, data):
        filterset = Filter.objects.filter(uid_id=data['uid_id'], stateid=data['stateid']).values()
        filterset = self.extendFilterWithTagInfo(data, filterset)
        filterset = self.categorizeFiltersIntoSystags(data, filterset)
        if len(filterset) == 0:
            return []
        else:
            filterset = self.simplifyObjToDateString(filterset)  # datetime to iso format
            return filterset

    def getDefaultFilterDataArray(self, data, isSignup=True):
        if isSignup:
            return [int(data['stateid']), data['tagid'], N_START_TIME, N_STOP_TIME, 1, 0, int(data['uid']),IS_CHECKED_DEFAULT]
        else:
            return [int(data['stateid']), data['tagid'], N_START_TIME, N_STOP_TIME, 1, 0, int(data['uid']),0]
        
    def addFilterAndTag(self, request):
        data = self.readData(request)
        data['tagid'] = Tag().addTag(data)

        if 'f_start_time' in data:
            values = [int(data['stateid']), data['tagid'], data['f_start_time'], data['f_stop_time'], data['f_repeat'],
                      data['f_visibility'], int(data['uid']), IS_CHECKED_DEFAULT]
        else:
            values = self.getDefaultFilterDataArray(data)
        self.addFilter(values)
        return self.createResultSet({'tagid': data['tagid']})

    # arguments 'data' need to be a list including values that will be stored into filter 
    def addFilter(self, data):
        args = dict([('table', 'filter'), ('values', data)])
        SQLExecuter().doInsertData(args)

    def addDefaultFilter(self, data, isSignup=True):
        for i in range(0, N_SYSTEM_TAGS):
            data['tagid'] = i
            if isSignup:
                values = self.getDefaultFilterDataArray(data)
            else:
                values = self.getDefaultFilterDataArray(data, False)
            self.addFilter(values)
        return i

    def deleteFilter(self, request):
        data = self.readData(request)
        args = {}
        args['table'] = 'Filter'
        args['attributes'] = [{'field': 'tagid', 'logic': 'And'}, {'field': 'uid', 'logic': 'And'},
                              {'field': 'stateid', 'logic': 'And'}]
        args['values'] = [data['tagid'], data['uid'], data['stateid']]
        SQLExecuter().doDeleteData(args)
        return self.createResultSet(data)

    def updateFilter(self, request):
        data = self.readData(request)
        if data['f_repeat'] == 'on':
            data['f_repeat'] = 1
        else:
            data['f_repeat'] = 0
        
        args               = {}
        args['table']      = 'Filter'
        args['attributes'] = ['f_start_time', 'f_stop_time', 'f_repeat', 'f_visibility']
        args['values']     = [data['f_start_time'], data['f_stop_time'], data['f_repeat'], data['f_visibility'], data['stateid'], data['uid'], data['tagid']]
        args['conditions'] = [{'field':'stateid', 'logic': 'And'}, {'field':'uid', 'logic': 'And'}, {'field':'tagid','logic': 'And'}]
        SQLExecuter().doUpdateData(args)
        
        '''
        Filter.objects.filter(stateid=data['stateid'], uid=data['uid'], tagid=data['tagid']).update(
            f_start_time=data['f_start_time'], f_stop_time=data['f_stop_time'], f_repeat=data['f_repeat'],
            f_visibility=data['f_visibility'])
            '''
        return self.createResultSet(data)

    def activateFilter(self, request):
        data = self.readData(request)
        objFilter = Filter.objects.filter(tagid=data['tagid'], stateid=data['stateid'], uid=data['uid'])
        if objFilter.count() == 0 and int(data['tagid']) < N_SYSTEM_TAGS:
            values = self.getDefaultFilterDataArray(data)
            self.addFilter(values)
        else:
            objFilter.update(is_checked=data['is_checked'])
        return self.createResultSet(data)

    def retrieveFilter(self, request):
        data = self.readData(request)
        objFilter = Filter.objects.filter(tagid=data['tagid'], stateid=data['stateid'], uid=data['uid']).values()[0]
        objFilter['tag_name'] = Tag.objects.get(tagid=data['tagid']).tag_name
        return self.createResultSet(objFilter)

class Note(models.Model, HttpRequestResponser, Formatter):
    note = models.CharField(max_length=140)
    n_timestamp = models.DateTimeField()
    link = models.TextField(blank=True)
    noteid = models.IntegerField(primary_key=True)
    uid = models.ForeignKey('User', db_column='uid')
    radius = models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)
    n_visibility = models.IntegerField()
    n_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    n_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_comment = models.IntegerField()
    n_like = models.IntegerField()

    class Meta:
        db_table = 'note'

    def getNewNoteid(self):
        if len(Note.objects.all().values()) == 0:
            return 1
        else:
            notetuple = Note.objects.all().order_by('noteid').latest('noteid')
            ##print tag.tagid
            return notetuple.noteid + 1

    def addNote(self, data):
        newNoteid = self.getNewNoteid()
        '''
        notetime = Note()
        notetime.note = data['note']
        #notetime.n_timestamp = timezone.now()
        print "======Insert time======"
        notetime.n_timestamp = JingoTimezone().getLocalTime()
        notetime.link = ''
        notetime.noteid = newNoteid
        notetime.uid = User(uid=data['uid'])

        if 'radius' in data:
            notetime.radius = data['radius']
            notetime.n_visibility = data['n_visibility']
            if 'is_comment' in data:
                notetime.is_comment = data['is_comment']
            else:
                notetime.is_comment = 0
        else:
            notetime.radius = N_DEFAULT_RADIUS     # default 200 yards
            notetime.n_visibility = 0                    # default 0: public
            notetime.is_comment = IS_COMMENT

        notetime.n_latitude = data['n_latitude']
        notetime.n_longitude = data['n_longitude']
        notetime.n_like = N_LIKES
        notetime.save()
        '''
        if 'radius' in data:
            radius = data['radius']
            n_visibility = data['n_visibility']
            if 'is_comment' in data:
                is_comment = data['is_comment']
            else:
                is_comment = 0
        else:
            radius = N_DEFAULT_RADIUS     # default 200 yards
            n_visibility = 0                    # default 0: public
            is_comment = IS_COMMENT
        
        data['n_longitude'] = "%.6f" % float(data['n_longitude'])
        data['n_latitude']  = "%.6f" % float(data['n_latitude'])
        timestamp = JingoTimezone().getLocalTime()
        values = [data['note'], timestamp, data['link'], newNoteid, data['uid'], radius, n_visibility, data['n_latitude'], data['n_longitude'], is_comment, N_LIKES]
        #print values
        args = dict([('table', 'note'), ('values', values)])
        SQLExecuter().doInsertData(args)
        
        data['noteid'] = newNoteid
        return data

    def plusLike(self, data):
        data['n_like'] = int(Note.objects.get(noteid=data['noteid']).n_like) + 1
        Note.objects.filter(noteid=data['noteid']).update(n_like=data['n_like'])
        return data

    def filterNotes(self, data):
        #nowtime = timezone.now()
        nowtime = JingoTimezone.getLocalTime()
        # retrieve user filter
        uCTags = self.getUserCategoryTagsList(data)

        # retrieve notesets
        nlist1 = Note_Time.objects.filter(n_repeat=0, n_start_time__lte=nowtime, n_stop_time__gte=nowtime).values(
            'noteid')
        nlist2 = Note_Time.objects.raw(
            "Select noteid From Note_Time Where n_repeat=1 And Time(Now()) Between Time(n_start_time) And Time(n_stop_time)").values(
            'noteid')
        nlist = nlist1 + nlist2
        notesets = Note.objects.filter(n_visibility__in=[0, 1], noteid__in=nlist)
        return data

class Note_Tag(models.Model, HttpRequestResponser, Formatter):
    noteid = models.ForeignKey('Note', db_column='noteid', primary_key=True)
    tagid = models.ForeignKey('Tag', db_column='tagid', primary_key=True)

    class Meta:
        db_table = 'note_tag'

    def addNoteTag(self, data):
        args = dict([('table', 'note_tag'), ('values', [data['noteid'], data['tagid']])])
        SQLExecuter().doInsertData(args)
        return data

    def addMultipleNoteTags(self, data):
        if 'tagids' in data and type(data['tagids']) == list and len(data['tagids']) > 1:
            tags = data['tagids']
            for tag in tags:
                data['tagid'] = tag
                Note_Tag().addNoteTag(data)
        elif 'tagids' in data:
            data['tagid'] = data['tagids']
            Note_Tag().addNoteTag(data)

        # add tags from tag_names
        self.addNoteTagFromTagName(data)

        # add a default tag (all)
        data['tagid'] = 0
        #print data
        Note_Tag().addNoteTag(data)
        #print "finished"
        return data

    def parseTagNames(self, data, stag_name):
        pos = stag_name.index(SPLITTER_SYMBOL)
        data['sys_tagid'] = stag_name[:pos]
        data['tag_name'] = stag_name[pos + 1:]
        return data

    def addNoteTagFromTagName(self, data):
        if 'tag_names' in data and type(data['tag_names']) is list and len(data['tag_names']) > 1:
            for stag_name in data['tag_names']:
                data = self.parseTagNames(data, stag_name)
                data['tagid'] = Tag().addTag(data)
                Note_Tag().addNoteTag(data)

        elif 'tag_names' in data:
            data = self.parseTagNames(data, data['tag_names'])
            data['tagid'] = Tag().addTag(data)
            Note_Tag().addNoteTag(data)

    def deleteNoteTag(self, request):
        data = self.readData(request)
        Note_Tag.objects.filter(tagid=data['tagid'], noteid=data['noteid']).delete()
        return 0

class Note_Time(models.Model, HttpRequestResponser, Formatter):
    timeid = models.IntegerField(primary_key=True)
    noteid = models.ForeignKey('Note', db_column='noteid')
    n_start_time = models.DateTimeField()
    n_stop_time = models.DateTimeField(null=True, blank=True)
    n_repeat = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'note_time'

    def getNewNoteTimeid(self):
        if len(Note_Time.objects.all().values()) == 0:
            return 1
        else:
            notetime = Note_Time.objects.all().order_by('timeid').latest('timeid')
            return notetime.timeid + 1

    def addNoteTime(self, data):
        newNoteTimeid = self.getNewNoteTimeid()
        notetime = Note_Time()
        notetime.timeid = newNoteTimeid
        notetime.noteid = Note(noteid=data['noteid'])
        notetime.n_start_time = data['n_start_time']
        notetime.n_stop_time = data['n_stop_time']
        notetime.n_repeat = data['n_repeat']
        notetime.save()
        return data

    def addNoteTimeRange(self, data):
        if 'n_repeat' not in data:
            data['n_repeat'] = 0

        if len(data['n_start_time']) == 0 or len(data['n_stop_time']) == 0:
            localtime            = JingoTimezone().getLocalTime()
            data['n_start_time'] = localtime
            data['n_stop_time']  = localtime + datetime.timedelta(days=1)

        Note_Time().addNoteTime(data)

class State(models.Model, HttpRequestResponser, Formatter):
    stateid = models.IntegerField(primary_key=True)
    state_name = models.CharField(max_length=45)
    uid = models.ForeignKey('User', db_column='uid', primary_key=True)
    is_current = models.IntegerField()

    class Meta:
        db_table = 'state'

    def getNewStateid(self):
        if len(State.objects.all().values()) == 0:
            return 1
        else:
            ustate = State.objects.all().order_by('uid', 'stateid').latest('stateid')
        return ustate.stateid + 1

    def getUserStatesList(self, data):
        return State.objects.all().filter(uid=data['uid']).order_by('is_current').reverse().values()

    def getUserStatesAndFiltersList(self, data):
        filt     = Filter()
        datalist = []
        uslist   = self.getUserStatesList(data)  # get user's all states
        #print len(uslist)
        for state in uslist:
            filterset        = filt.getUserStateFilters(state)
            state['filters'] = filterset
            datalist.append(state)
        return datalist

    def setDefaultState(self, request):
        data = self.readData(request)
        State.objects.all().update(is_current=0)
        State.objects.filter(stateid=data['stateid'], uid=data['uid']).update(is_current=1)
        return self.createResultSet(data)

    def insertState(self, uid, is_current, stateid):
        data = [stateid, STATE_NAME_DEFAULT, uid, is_current]
        args = dict([('table', 'State'), ('values', data)])
        SQLExecuter().doInsertData(args)

    def addState(self, request, mode='user-defined'):

        if mode == 'default': 
            self.insertState(request['uid'], 1, 0)
            data = State.objects.filter(stateid=0, uid=request['uid']).values()
            return data
        else:
            request             = self.readData(request)
            newStateid          = self.getNewStateid()
            self.insertState(request['uid'], 0, newStateid)
            newState            = State.objects.filter(stateid=newStateid).values()[0]
            newState['uid']     = request['uid'] 
            ufilter             = Filter().addDefaultFilter(newState, False)
            newState['filters'] = Tag().getSysTags()
            data                = dict([('state', newState)])
            return self.createResultSet(data)

    def deleteState(self, request):
        data = self.readData(request)
        args = {}
        args['table'] = 'State'
        args['attributes'] = [{'field': 'stateid', 'logic': 'And'}, {'field': 'uid', 'logic': 'And'}]
        args['values'] = [data['stateid'], data['uid']]
        SQLExecuter().doDeleteData(args)
        return self.createResultSet(data)

    def updateState(self, request):
        data = self.readData(request)
        State.objects.filter(stateid=data['stateid'], uid=data['uid']).update(state_name=data['state_name'])
        return self.createResultSet(data)

class Tag(models.Model, HttpRequestResponser, Formatter):
    tagid = models.IntegerField(primary_key=True)
    tag_name = models.CharField(max_length=45)
    uid = models.ForeignKey('User', null=True, db_column='uid', blank=True)
    sys_tagid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'tag'

    def getSysTags(self, type='omit'):
        if type == 'omit':
            return Tag.objects.order_by('tagid').filter(tagid__gte=1, tagid__lte=10).values()
        return Tag.objects.order_by('tagid').filter(tagid__gte=0, tagid__lte=10).values()

    def getNewTagid(self):
        if len(Tag.objects.all().values()) == 0:
            return 1
        else:
            tag = Tag.objects.all().order_by('tagid').latest('tagid')
            return tag.tagid + 1

    def getUserSysTags(self, data):
        result = []
        args = {}
        args['columns'] = ['b.*, a.tag_name, a.sys_tagid']
        args['tables'] = ['tag as a', 'filter as b']
        args['joins'] = ['a.tagid = b.tagid', 'a.tagid>=%s And a.tagid<=%s']
        args['conditions'] = [{'criteria': 'b.uid=', 'logic': 'And'}, {'criteria': 'b.stateid=', 'logic': 'And'}]
        args['values'] = [0, 10, data['uid_id'], data['stateid']]
        slist = SQLExecuter().doSelectData(args)
        for sys in slist:
            sys['is_checked'] = 0
            result.append(sys)
        return result

    def getUserTagsList(self, request):
        data = self.readData(request)
        data['uid'] = '1'
        taglist = list(Tag.objects.filter(uid=data['uid']).order_by('tagid').values())
        defaultlist = list(Tag.objects.filter(uid=None).order_by('tagid').values())
        data = dict([('tagslist', taglist + defaultlist)])
        return self.createResultSet(data)

    def getUserCategoryTagsList(self, data):
        tmp = []
        result = []
        taglist = list(Tag.objects.filter(uid=data['uid']).order_by('tagid').values())
        defaultlist = list(Tag.objects.filter(uid=None).order_by('tagid').values())

        for dtag in defaultlist[1:]:
            dtag['tags'] = []
            tmp.append(dtag)

        for row in tmp:
            for tag in taglist:
                if tag['sys_tagid'] == row['sys_tagid']:
                    row['tags'].append(tag)
            result.append(row)

        return result

    def addTag(self, data):
        newTagid = self.getNewTagid()
        tag = Tag()
        tag.tagid = newTagid
        tag.tag_name = data['tag_name']
        tag.uid = User(uid=int(data['uid']))
        tag.sys_tagid = data['sys_tagid']
        tag.save()
        return newTagid

    def deleteTag(self, request):
        data = self.readData(request)
        args = {}
        args['table'] = 'Tag'
        args['attributes'] = [{'field': 'stateid', 'logic': 'And'}, {'field': 'uid', 'logic': 'And'}]
        args['values'] = [data['tagid'], data['uid']]
        SQLExecuter().doDeleteData(args)
        return self.createResultSet(data)

    def updateTag(self, request):
        data = self.readData(request)
        data = Tag.objects.filter(tagid=data['tagid'], uid=data['uid']).update(state_name=data['tag_name'])
        return self.createResultSet(data)

class User(models.Model, HttpRequestResponser, Formatter):
    uid = models.IntegerField(primary_key=True)
    u_name = models.CharField(max_length=45)
    email = models.CharField(max_length=45)
    u_timestamp = models.DateTimeField()
    password = models.CharField(max_length=15)

    class Meta:
        db_table = 'user'

    def setUserSession(self, request, usr):
        data                          = self.getUserProfile(usr)
        request.session['uid']        = usr['uid']
        request.session['usrdata']    = data['usr']
        request.session['usrprofile'] = data

    def getNewUid(self):
        if len(User.objects.all().values()) == 0:
            return 1
        else:
            usr = User.objects.all().order_by('uid').latest('uid')
            ##print usr.uid
            return usr.uid + 1

        usr = User.objects.all().order_by('uid').latest('uid')
        ##print usr.uid
        return usr.uid + 1

    def getUserData(self, input_uid):
        return User.objects.filter(uid=input_uid).values()[0]

    def addUser(self, data):
        usr = User()
        usr.uid = self.getNewUid()
        usr.u_name = data['u_name']
        usr.email = data['email']
        usr.password = base64.b64encode(data['password'])
        #usr.u_timestamp = timezone.now()
        usr.u_timestamp = JingoTimezone().getLocalTime()
        usr.save()
        return User.objects.filter(email=data['email']).values()

    def signup(self, request):
        message, result, response = [{}, RESULT_FAIL, {}]
        verifier                  = DataVerifier()
        data                      = self.readData(request)
        
        if len(data) == 0:
            message['error'] = MESSAGE_REQUEST_ERROR
        else:
            # check username 
            if not len(data['u_name']) >= USERNAME_LENGTH:
                message['u_name'] = USERNAME_TOO_SHORT
            
            if not verifier.isValidFormat(data['u_name'], 'user'):
                message['u_name'] = USERNAME_INVALID
            
            # check email
            if not verifier.isValidFormat(data['email'], 'email'):
                message['email'] = EMAIL_INVAILD

            if not verifier.isEmailUnique(User.objects, data['email']):
                message['email'] = EMAIL_TAKEN
            
            # check password
            if not len(data['password']) >= PASSWORD_LENGTH:    
                message['password'] = PASSWORD_TOO_SHORT
                
            if not verifier.isValidFormat(data['password'], 'password'):
                message['password'] = PASSWORD_INVALID
            
            if not data['password'] == data['confirm_password']:
                message['password'] = PASSWORD_CONFIRM_ERROR
            
        if len(message) == 0:
            result                 = RESULT_SUCCESS
            response               = self.simplifyObjToDateString(self.addUser(data))[0]
            response['state_name'] = STATE_NAME_DEFAULT
            state                  = State().addState(response, 'default')[0]
            state['uid']           = state['uid_id']
            ufilter                = Filter().addDefaultFilter(state)
            self.setUserSession(request, response)
        
        return self.createResultSet(response, result, message)

    def login(self, request):
        message, result, response = [{}, RESULT_FAIL, {}]
        
        if request.session.get('uid', False):
            result = RESULT_SUCCESS
        else:
            check = []
            data  = self.readData(request)
            
            if len(data) == 0:
                message['error'] = MESSAGE_REQUEST_ERROR
            else:
                check = User.objects.filter(email=data['email']).values()
                
            if len(check) == 0:
                message['email'] = MESSAGE_EMAIL_ERROR

            if len(check) > 0 and base64.b64decode(check[0]['password']) != data['password']:
                message['password'] = MESSAGE_PASSWORD_ERROR

            if len(check) > 0 and base64.b64decode(check[0]['password']) == data['password']:
                result   = RESULT_SUCCESS
                response = self.simplifyObjToDateString(check)[0]
                self.setUserSession(request, response)
        
        return self.createResultSet(response, result, message)
    
    def logout(self, request):
        try:
            del request.session['uid']
            request.session.clear()
        except KeyError:
            message = LOGOUT_FAIL
            return self.createResultSet({}, RESULT_FAIL, message)
        message = LOGOUT_SUCCESS
        return self.createResultSet({}, RESULT_SUCCESS, message)

    def getUserProfile(self, data):
        uid  = data['uid']
        usr  = self.getUserData(uid)
        data = dict([('usr', usr), ('stateslist', State().getUserStatesAndFiltersList(usr))])
        return data
    
    def postNote(self, request):
        dataset = []
        data    = self.readData(request)
        data    = Note().addNote(data)
        Note_Time().addNoteTimeRange(data)
        Note_Tag().addMultipleNoteTags(data)
        dataset.append(data)
        data = self.simplifyObjToDateString(dataset)
        # update to session
        #print request.session['noteslist']
        request.session['noteslist'].append(data[0])
        #print request.session['noteslist']
        return self.createResultSet(data)

    def clickLike(self, request):
        data = self.readData(request)
        data = Note().plusLike(data)
        return self.createResultSet(data)

    def postComment(self, request):
        dataset = []
        data = self.readData(request)
        data['commentid'] = Comments().addComment(data)
        data['u_name'] = User.objects.filter(uid=data['uid']).values('u_name')[0]['u_name']
        data['c_timestamp'] = Comments.objects.filter(commentid=data['commentid']).values()[0]['c_timestamp']
        dataset.append(data)
        data = self.simplifyObjToDateString(dataset, NORMAL_DATE_PATTERN)[0]
        return self.createResultSet(data)

    def searchNotes(self, request):
        data              = self.readData(request)
        noteslist         = NoteFilter().retrieveNotesByKeywords(data)
        data['noteslist'] = self.simplifyObjToDateString(noteslist, NORMAL_DATE_PATTERN)
        request.session['noteslist'] = data['noteslist']
        return self.createResultSet(data)

    def receiveNotes(self, request):
        data                         = self.readData(request)
        data['noteslist']            = self.simplifyObjToDateString(NoteFilter().filterNotes(data), NORMAL_DATE_PATTERN)
        request.session['noteslist'] = data['noteslist']
        return self.createResultSet(data)

    def readNote(self, request):
        data                  = self.readData(request)
        note                  = Note.objects.filter(noteid=data['noteid']).values()[0]
        reader                = str(request.session['uid'])
        poster                = str(note['uid_id'])
        
        if reader != poster:
            note['is_friendship'] = Friend().checkFriendship(reader, poster)
        else:
            note['is_friendship'] = 4
                    
        comments             = Comments().retrieveComments(data)
        note['n_comments']   = len(comments)
        note['commentslist'] = comments
        note['poster']       = User.objects.filter(uid=poster).values()[0]

        return self.createResultSet(note)
    
    def unfollow(self, request):
        data = self.readData(request)
        Friend().cancelFriendship(data)
        return self.createResultSet(data)
    
    def sendInvitation(self, request):
        data = self.readData(request)
        data = Friend().addInvitation(data)
        return self.createResultSet(data)
    
    def replyInvitation(self, request):
        data = self.readData(request)
        data = Friend().responseInvitation(data)
        return self.createResultSet(data)
    
    def initFriendArea(self, request):
        data                  = {}
        data['uid']           = request.session['uid']
        data['is_friendship'] = 1
        flist                 = Friend().getFriendsInfoList(data)
        data['is_friendship'] = 2
        plist                 = Friend().getPendingsInfoList(data)
        data                  = dict([('friendslist', flist), ('n_friends', len(flist)), ('pendingslist', plist), ('n_pendings', len(plist))])
        return self.createResultSet(data)
    
class NoteFilter(HttpRequestResponser, Formatter):
    def __init__(self):
        self.sql = SQLExecuter()

    def getValuesBasedonKey(self, valueset, key):
        result = []
        for row in valueset:
            result.append(row[key])
        return result

    def getKeywordString(self, data):
        result, keywordset, sql = [{}, [], '']
        keywords = string.split(data['keywords'], ' ')
        
        # log keywords the user uses and his location
        Log_Keywords().logUserKeywords(data, keywords)
        
        # make query string
        for word in keywords:
            keywordset.append('%' + word + '%')
            keywordset.append('%' + word + '%')
            sql += '(a.note like %s Or c.tag_name like %s) And '
        
        result['sql']        = '(' + sql[:len(sql) - 5] + ')'
        result['keywords']   = keywordset
        result['n_keywords'] = len(keywordset)
        return result
    
    def getNoteInfoListByKewords(self, data, currenttime):
        #data['keywords'] = '%' + data['keywords'] + '%'
        keywordset  = self.getKeywordString(data)
        #strSQL = "Select a.*, b.tagid, c.sys_tagid, c.tag_name, d.n_start_time, d.n_stop_time, n_repeat From note as a, note_tag as b, tag as c, (Select * From note_time Where %s between n_start_time And n_stop_time And n_repeat=0) as d Where a.noteid=b.noteid And b.tagid=c.tagid And a.noteid=d.noteid And (a.note like %s Or c.tag_name like %s) Union Select a.*, b.tagid, c.sys_tagid, c.tag_name, d.n_start_time, d.n_stop_time, n_repeat From note as a, note_tag as b, tag as c, (Select * From note_time Where %s between n_start_time And n_stop_time And n_repeat=1) as d Where a.noteid=b.noteid And b.tagid=c.tagid And a.noteid=d.noteid And (a.note like %s Or c.tag_name like %s)"
        strSQL      = "Select a.*, b.tagid, c.sys_tagid, c.tag_name, d.n_start_time, d.n_stop_time, n_repeat From note as a, note_tag as b, tag as c, (Select * From note_time Where %s between n_start_time And n_stop_time And n_repeat=0) as d Where a.noteid=b.noteid And b.tagid=c.tagid And a.noteid=d.noteid And %s Union Select a.*, b.tagid, c.sys_tagid, c.tag_name, d.n_start_time, d.n_stop_time, n_repeat From note as a, note_tag as b, tag as c, (Select * From note_time Where %s between n_start_time And n_stop_time And n_repeat=1) as d Where a.noteid=b.noteid And b.tagid=c.tagid And a.noteid=d.noteid And %s" % ('%s', keywordset['sql'], '%s',keywordset['sql'])
        
        values = keywordset['keywords'] * 2
        values.insert(0, currenttime)
        values.insert(int(keywordset['n_keywords']) + 1, currenttime)
        #print values
        noteslist   = self.sql.doRawSQL(strSQL, values)
        return noteslist

    def getNoteInfoList(self, currenttime):
        # retrieve every detail of notes
        strSQL = 'Select a.*, b.tagid, c.sys_tagid, d.n_start_time, d.n_stop_time, n_repeat From note as a, note_tag as b, tag as c, (Select * From note_time Where %s between n_start_time And n_stop_time And n_repeat=0) as d Where a.noteid=b.noteid And b.tagid=c.tagid And a.noteid=d.noteid Union Select a.*, b.tagid, c.sys_tagid, d.n_start_time, d.n_stop_time, n_repeat From note as a, note_tag as b, tag as c, (Select * From note_time Where %s between n_start_time And n_stop_time And n_repeat=1) as d Where a.noteid=b.noteid And b.tagid=c.tagid And a.noteid=d.noteid'
        noteslist = self.sql.doRawSQL(strSQL, [currenttime, currenttime])
        return noteslist

    def getUserCategoryTagsList(self, data):
        args = {}
        args['columns'] = ['b.*, c.sys_tagid']
        args['tables'] = ['state as a', 'filter as b', 'tag as c']
        args['joins'] = ['a.stateid=b.stateid And a.uid=b.uid And b.tagid=c.tagid And a.is_current=1 And is_checked=1']
        args['conditions'] = [{'criteria': 'b.uid=', 'logic': 'And'}]
        args['values'] = [data['uid']]
        uCTags = self.sql.doSelectData(args)
        return uCTags

    def computeDistance(self, data, n_longitude, n_latitude):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [float(n_longitude), float(n_latitude), float(data['u_longitude']),
                                               float(data['u_latitude'])])

        # haversine formula 
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        dist = (6367 * c) * 1093.61 # km to yard
        return dist

    def filterByTags(self, uProfile, noteslist):
        result = []
        passset = self.getValuesBasedonKey(uProfile, 'sys_tagid')
        for note in noteslist:
            if note['sys_tagid'] in passset:
                result.append(note)
        return result

    def filterByTime(self, uProfile, noteslist, currenttime):
        result      = []
        sys_tagset  = []
        currenttime = datetime.datetime.strptime(currenttime, '%Y-%m-%d %H:%M:%S')

        for filter in uProfile:
            if filter['f_repeat']:
                current = currenttime.strftime('%H:%M:%S')
                start   = filter['f_start_time'].strftime('%H:%M:%S')
                end     = filter['f_stop_time'].strftime('%H:%M:%S')
            else:
                current = currenttime.strftime('%Y-%m-%d %H:%M:%S')
                start   = filter['f_start_time']
                end     = filter['f_stop_time']
            #print "current %s" % current
            #print "start %s" % start
            #print "end %s" % end
            if current >= start and current <= end:
                sys_tagset.append(filter['sys_tagid'])
                
        #print "active sys_tagset"
        #print sys_tagset

        for note in noteslist:
            #print "note " + str(note['noteid']) + " has sys:" + str(note['sys_tagid'])
            if note['sys_tagid'] in sys_tagset:
                #print "note " + str(note['noteid']) + " passed"
                result.append(note)
        return result

    def filterByVisibility(self, data, uProfile, noteslist):
        friendslist = Friend().getFriendsList(data)
        
        #print "friendslist"
        #print friendslist
        # generalize visibility of user tags based on sys_tags
        sys_visset = {}
        result = []
        #print "current uProfile"
        #print uProfile
        for ufilter in uProfile:
            sys_tag    = ufilter['sys_tagid']
            visibility = ufilter['f_visibility']
            if (sys_tag in sys_visset and sys_visset[sys_tag] < visibility) or (sys_tag not in sys_visset):
                sys_visset[sys_tag] = visibility
        #print "visibility of sys_tag"
        #print sys_visset

        for note in noteslist:
            #print "with sys:" + str(note['sys_tagid']) + ", note " + str(note['noteid']) + " has vis:" + str(note['n_visibility']) + " while user has vis:" + str(sys_visset[note['sys_tagid']])
            case_a, case_b, case_c, case_d, case_e, case_f, case_g = [False, False, False, False, False, False, False]
            if note['sys_tagid'] in sys_visset:
                #print str(note['uid']) in friendslist
                # if both of them have visibilities of public
                if sys_visset[note['sys_tagid']] == 0 and note['n_visibility'] == 0:
                    case_a = True
                    #print "note " + str(note['noteid']) + " passed because of case_a"
                
                #if sys_visset[note['sys_tagid']] == 0 and note['n_visibility'] == 1 and (str(note['uid']) != str(data['uid']) and note['uid'] in friendslist):
                if sys_visset[note['sys_tagid']] == 0 and note['n_visibility'] == 1 and not ((str(note['uid']) != str(data['uid']) and note['uid'] not in friendslist)):
                    case_b = True
                    #print "note " + str(note['noteid']) + " passed because of case_b"   
                    
                if sys_visset[note['sys_tagid']] == 0 and note['n_visibility'] == 2 and str(note['uid']) == str(data['uid']):
                    case_c = True
                    #print "note " + str(note['noteid']) + " passed because of case_c"
                    
                if sys_visset[note['sys_tagid']] == 1 and note['n_visibility'] == 0 and not (str(note['uid']) != str(data['uid']) and note['uid'] not in friendslist):
                    case_d = True
                    #print "note " + str(note['noteid']) + " passed because of case_d"    
                    
                if sys_visset[note['sys_tagid']] == 1 and note['n_visibility'] == 1 and not (str(note['uid']) != str(data['uid']) and note['uid'] not in friendslist):
                    case_e = True
                    #print "note " + str(note['noteid']) + " passed because of case_e"  
                
                if sys_visset[note['sys_tagid']] == 1 and note['n_visibility'] == 2 and str(note['uid']) == str(data['uid']):
                    case_f = True
                    #print "note " + str(note['noteid']) + " passed because of case_f" 
                
                # if reader has private and he is poster also
                #print data['uid']
                #print note['uid']
                if sys_visset[note['sys_tagid']] == 2 and str(note['uid']) == str(data['uid']):
                    case_g = True
                    #print "note " + str(note['noteid']) + " passed because of case_g" 
                    
                if case_a or case_b or case_c or case_d or case_e or case_f or case_g:
                    result.append(note)
                    
                    '''
            if note['sys_tagid'] in sys_visset and sys_visset[note['sys_tagid']] == note['n_visibility']:
                if (note['n_visibility'] == 1 and note['uid'] in friendslist) or note['n_visibility'] == 0:
                    result.append(note)
                    '''
        #print "after visibility"
        #print result
        return result

    def filterByLocation(self, data, noteslist):
        result = []
        for note in noteslist:
            dist = self.computeDistance(data, note['n_longitude'], note['n_latitude'])
            if dist <= note['radius']:
                result.append(note)
        return result

    def filterNotes(self, data, mode='normal'):
        localtime   = JingoTimezone().getLocalTime()
        currenttime = localtime.strftime('%Y-%m-%d %H:%M:%S')
        if mode == 'normal':
            noteslist = self.getNoteInfoList(currenttime)
        else:
            noteslist = self.getNoteInfoListByKewords(data, currenttime)
        uProfile = self.getUserCategoryTagsList(data)

        # filter by user's tags
        noteslist = self.filterByTags(uProfile, noteslist)

        # filter by user's time range
        noteslist = self.filterByTime(uProfile, noteslist, currenttime)

        # filter by visibility and friendship
        noteslist = self.filterByVisibility(data, uProfile, noteslist)

        # filter by location
        noteslist = self.filterByLocation(data, noteslist)
        #print noteslist
        return noteslist

    def retrieveNotesByKeywords(self, data):
        return self.filterNotes(data, 'keyword')
        
class AdminArea(HttpRequestResponser):  
    
    def init(self):
        result = {}
        result['Statistic']       = self.getStatistic()
        result['AreasRanking']    = self.getAreasRanking()
        result['KeywordsRanking'] = self.getKeywordsRanking()
        result['NotesRanking']    = self.getNotesRanking()
        result['PosterRanking']   = self.getPosterRanking()
        result['TagsRanking']     = self.getTagsRanking()
        return self.createResultSet(result)
        
    def getStatistic(self):
        strSQL = 'Select * From v_statistic'
        result = SQLExecuter().doRawSQL(strSQL)
        return result
    
    def getAreasRanking(self):
        strSQL = 'Select n_longitude, n_latitude, n_notes, top_tag From v_areas_ranking'
        result = SQLExecuter().doRawSQL(strSQL)
        return result
    
    def getKeywordsRanking(self):
        strSQL = 'Select * From v_keywords_ranking'
        result = SQLExecuter().doRawSQL(strSQL)
        return result
    
    def getNotesRanking(self):
        strSQL = 'Select * From v_notes_ranking'
        result = SQLExecuter().doRawSQL(strSQL)
        return result

    def getPosterRanking(self):
        strSQL = 'Select u_name, n_notes From v_poster_ranking'
        result = SQLExecuter().doRawSQL(strSQL)
        return result
    
    def getTagsRanking(self):
        strSQL = 'Select tag_name, n_notes From v_tags_ranking'
        result = SQLExecuter().doRawSQL(strSQL)
        return result
      