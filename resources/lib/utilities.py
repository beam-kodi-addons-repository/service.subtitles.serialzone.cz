# -*- coding: utf-8 -*- 

import os, sys
import xbmc, xbmcvfs
from struct import Struct
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

def get_file_size(filename, is_rar):
    try:
        if is_rar:
            file_size = get_file_size_from_rar(filename)
            return -1 if file_size == None else file_size
        else:
            return xbmcvfs.Stat(filename).st_size()
    except:
        return -1

# Based on https://github.com/markokr/rarfile/blob/master/rarfile.py
def get_file_size_from_rar(first_rar_filename):

    log_name = __name__ + " [RAR]"

    RAR_BLOCK_MAIN          = 0x73 # s
    RAR_BLOCK_FILE          = 0x74 # t
    RAR_FILE_LARGE          = 0x0100
    RAR_ID = str("Rar!\x1a\x07\x00")

    S_BLK_HDR = Struct('<HBHH')
    S_FILE_HDR = Struct('<LLBLLBBHL')
    S_LONG = Struct('<L')

    fd = xbmcvfs.File(first_rar_filename)
    if fd.read(len(RAR_ID)) == RAR_ID:
        log(log_name, "Reading file headers")
        while True:

            buf = fd.read(S_BLK_HDR.size)
            if not buf: return None

            t = S_BLK_HDR.unpack_from(buf)
            header_crc, header_type, header_flags, header_size = t
            pos = S_BLK_HDR.size

            # read full header
            header_data = buf + fd.read(header_size - S_BLK_HDR.size) if header_size > S_BLK_HDR.size else buf

            if len(header_data) != header_size: return None # unexpected EOF?

            if header_type == RAR_BLOCK_MAIN:
                log(log_name, "Main block found")
                continue
            elif header_type == RAR_BLOCK_FILE:
                log(log_name, "File block found")
                file_size = S_FILE_HDR.unpack_from(header_data, pos)[1]
                log(log_name, "File in rar size: %s" % file_size)
                if header_flags & RAR_FILE_LARGE: # Large file support
                    log(log_name, "Large file flag")
                    file_size |= S_LONG.unpack_from(header_data, pos + S_FILE_HDR.size + 4)[0] << 32
                    log(log_name, "File in rar size: %s after large file" % file_size)
                return file_size
            else:
                log(__name__, "RAR unknown header type %s" % header_type)
                return None
    else:
        return None

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
