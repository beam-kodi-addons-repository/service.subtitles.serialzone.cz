# -*- coding: utf-8 -*- 

import os, sys
import xbmc, xbmcvfs
import struct
import urllib

from datetime import datetime
import time

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

def log(module, msg):
    xbmc.log((u"### [%s] - %s" % (module, msg,)).encode('utf-8'), level=xbmc.LOGDEBUG)

def copy_subtitles_on_rar(subtitle_list,lang):
    if not subtitle_list: return False

    file_original_path = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path of a playing file
    if (file_original_path.find("rar://") > -1):
        file_original_path = os.path.dirname(file_original_path[6:])

        # take first subtitles in subtitle_list
        subtitles_path = subtitle_list[0]
        file_original_dir = os.path.dirname(file_original_path)
        file_original_basename = os.path.basename(file_original_path)
        file_original_name, file_original_ext = os.path.splitext(file_original_basename)

        subtitles_basename = os.path.basename(subtitles_path)
        subtitles_name, subtitles_ext = os.path.splitext(subtitles_basename)

        short_lang = xbmc.convertLanguage(lang,xbmc.ISO_639_1)

        final_destination = os.path.join(file_original_dir, file_original_name + "." + short_lang + subtitles_ext)

        result = (xbmcvfs.copy(subtitles_path, final_destination) == 1)
        log(__name__,"[RAR] Copy subtitle: %s result %s" % ([subtitles_path, final_destination], result))
        return result
    else:
        return False

def get_current_episode_first_air_date():

    json_query = xbmc.executeJSONRPC('{ \
         "jsonrpc": "2.0", \
         "method": "Player.GetActivePlayers", \
         "id": "PlayerID" }'
    )
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    jsonobject = simplejson.loads(json_query)
    if jsonobject.has_key('result') and jsonobject['result'].__len__() > 0:
      playerid = jsonobject['result'][0]['playerid']
    else:
      return None

    json_query = xbmc.executeJSONRPC('{ \
        "jsonrpc": "2.0", \
        "method": "Player.GetItem", \
        "params": { "properties": ["firstaired"], "playerid": %s },\
        "id": "EpisodeGetItem" }' % playerid)
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    jsonobject = simplejson.loads(json_query)
    if jsonobject.has_key('result') and jsonobject['result'].has_key('item'):
        first_air_date = jsonobject['result']['item']['firstaired']
        if first_air_date == '': return None

    if first_air_date == "1969-12-31":
        log(__name__, "First air date 1969-12-31 => None")
        return None

    # http://forum.xbmc.org/showthread.php?tid=112916
    date_format = "%Y-%m-%d"
    try:
        first_air_date = datetime.strptime(first_air_date, date_format).date()
    except TypeError:
        first_air_date = datetime(*(time.strptime(first_air_date, date_format)[0:6])).date()

    log(__name__, "Current epoisode first air date: %s" % first_air_date)
    return first_air_date

def file_size_and_hash(filename, rar):
	try:
		file_size, file_hash = hashFile(filename, rar)
	except:
		file_size, file_hash = -1, None
	return file_size, file_hash

def extract_subtitles(archive_dir):
	xbmc.executebuiltin(('XBMC.Extract("%s")' % archive_dir).encode('utf-8'))
	xbmc.sleep(1000)
	basepath = os.path.dirname(archive_dir)
	extracted_files = os.listdir(basepath)
	exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
	extracted_subtitles = []
	if len(extracted_files) < 1 :
		return []
	else:
		for extracted_file in extracted_files:
			if os.path.splitext(extracted_file)[1] in exts:
				extracted_subtitles.append(os.path.join(basepath, extracted_file))
	return extracted_subtitles

def hashFile(file_path, rar):
    if rar:
      return hashRar(file_path)

    log( __name__,"Hash Standard file")
    longlongformat = 'q'  # long long
    bytesize = struct.calcsize(longlongformat)
    f = xbmcvfs.File(file_path)

    filesize = f.size()
    hash = filesize

    if filesize < 65536 * 2:
        return "SizeError"

    buffer = f.read(65536)
    f.seek(max(0,filesize-65536),0)
    buffer += f.read(65536)
    f.close()
    for x in range((65536/bytesize)*2):
        size = x*bytesize
        (l_value,)= struct.unpack(longlongformat, buffer[size:size+bytesize])
        hash += l_value
        hash = hash & 0xFFFFFFFFFFFFFFFF

    returnHash = "%016x" % hash
    return filesize,returnHash


def hashRar(firsrarfile):
    log( __name__,"Hash Rar file")
    f = xbmcvfs.File(firsrarfile)
    a=f.read(4)
    if a!='Rar!':
        raise Exception('ERROR: This is not rar file.')
    seek=0
    for i in range(4):
        f.seek(max(0,seek),0)
        a=f.read(100)
        type,flag,size=struct.unpack( '<BHH', a[2:2+5])
        if 0x74==type:
            if 0x30!=struct.unpack( '<B', a[25:25+1])[0]:
                raise Exception('Bad compression method! Work only for "store".')
            s_partiizebodystart=seek+size
            s_partiizebody,s_unpacksize=struct.unpack( '<II', a[7:7+2*4])
            if (flag & 0x0100):
                s_unpacksize=(unpack( '<I', a[36:36+4])[0] <<32 )+s_unpacksize
                log( __name__ , 'Hash untested for files biger that 2gb. May work or may generate bad hash.')
            lastrarfile=getlastsplit(firsrarfile,(s_unpacksize-1)/s_partiizebody)
            hash=addfilehash(firsrarfile,s_unpacksize,s_partiizebodystart)
            hash=addfilehash(lastrarfile,hash,(s_unpacksize%s_partiizebody)+s_partiizebodystart-65536)
            f.close()
            return (s_unpacksize,"%016x" % hash )
        seek+=size
    raise Exception('ERROR: Not Body part in rar file.')

def getlastsplit(firsrarfile,x):
    if firsrarfile[-3:]=='001':
        return firsrarfile[:-3]+('%03d' %(x+1))
    if firsrarfile[-11:-6]=='.part':
        return firsrarfile[0:-6]+('%02d' % (x+1))+firsrarfile[-4:]
    if firsrarfile[-10:-5]=='.part':
        return firsrarfile[0:-5]+('%1d' % (x+1))+firsrarfile[-4:]
    return firsrarfile[0:-2]+('%02d' %(x-1) )

def addfilehash(name,hash,seek):
    f = xbmcvfs.File(name)
    f.seek(max(0,seek),0)
    for i in range(8192):
        hash+=struct.unpack('<q', f.read(8))[0]
        hash =hash & 0xffffffffffffffff
    f.close()
    return hash

