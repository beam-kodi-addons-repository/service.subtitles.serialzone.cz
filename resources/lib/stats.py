import sys, os
import xbmc
from uuid import uuid4

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

def log(module, msg):
	xbmc.log((u"### [%s] - %s" % (module, msg,)).encode('utf-8'), level=xbmc.LOGDEBUG)

def get_uuid(addon):
	try:
		profile_pwd = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
		uuid_file = os.path.join(profile_pwd, "uuid.txt")
		my_uuid = None

		if os.path.isfile(uuid_file):
			f = open(uuid_file, "r")
		 	my_uuid = f.read()
		 	f.close()

		if not my_uuid:
	 		my_uuid = str(uuid4())
	 		f = open(uuid_file, "w")
	 		f.write(my_uuid)
	 		f.close()

	 	return my_uuid
	except:
	 	return ""


def send_statistics(action, addon, title, item, result_count):

	data = xbmc.executeJSONRPC('{"jsonrpc" : "2.0", "method": "XBMC.GetInfoLabels", "id" :1, "params": {"labels" : ["System.BuildVersion","System.ScreenHeight","System.ScreenWidth","System.KernelVersion","System.Language"]}}')  
	data = simplejson.loads(data)
	try:
		info = {}

		info['xbmc_uniq_id']			= get_uuid(addon)

		info['xbmc_screen_resolution'] 	= '%sx%s' %(data['result']['System.ScreenWidth'],data['result']['System.ScreenHeight'])
		info['xbmc_language'] 			= data['result']['System.Language']
		info['xbmc_build_version'] 		= data['result']['System.BuildVersion']
		
		info['system_platform'] 		= sys.platform
		
		info['addon_id'] 				= addon.getAddonInfo('id')
		info['addos_version'] 			= addon.getAddonInfo('version')

		info['search_title'] 			= title
		info['search_results_count'] 	= result_count
		info['search_languages']		= item['3let_language']

		info['input_rar'] 				= item['rar']
		info['input_man_search'] 		= item['mansearch']
		info['input_year'] 				= item['year']
		info['input_season_num']		= item['season']
		info['input_episode_num']		= item['episode']
		info['input_tvshow']			= item['tvshow']
		info['input_title']				= item['title']

		log(__name__, info)
		return True
	except:
		return False

