

class Plugin_OBJ():

    def __init__(self, plugin_utils):
        self.plugin_utils = plugin_utils

        self.channels_json_url = "https://iptv-org.github.io/api/channels.json"
        self.streams_json_url = "https://iptv-org.github.io/api/streams.json"

        self.filter_dict = {}
        self.setup_filters()

        self.unfiltered_chan_json = None
        self.filtered_chan_json = None

    @property
    def filtered_chan_list(self):
        if not self.filtered_chan_json:
            self.filtered_chan_json = self.filterlist()
        return self.filtered_chan_json

    @property
    def unfiltered_chan_list(self):
        if not self.unfiltered_chan_json:
            self.unfiltered_chan_json = self.get_unfiltered_chan_json()
        return self.unfiltered_chan_json

    def setup_filters(self):

        for x in ["countries", "languages", "category"]:
            self.filter_dict[x] = []

        for filter in list(self.filter_dict.keys()):

            filterconf = self.plugin_utils.config.dict["iptvorg"]["filter_%s" % filter]
            if filterconf:
                if isinstance(filterconf, str):
                    filterconf = [filterconf]
                self.plugin_utils.logger.info("Found %s Enabled %s Filters" % (len(filterconf), filter))
                self.filter_dict[filter].extend(filterconf)
            else:
                self.plugin_utils.logger.info("Found No Enabled %s Filters" % (filter))

    def get_channels(self):

        channel_list = []

        self.plugin_utils.logger.info("Pulling Unfiltered Channels: %s" % self.channels_json_url)
        self.unfiltered_chan_json = self.get_unfiltered_chan_json()
        self.plugin_utils.logger.info("Found %s Total Channels" % len(self.unfiltered_chan_json))

        self.filtered_chan_json = self.filterlist()
        self.plugin_utils.logger.info("Found %s Channels after applying filters and Deduping." % len(self.filtered_chan_list))

        for channel_dict in self.filtered_chan_list:
            clean_station_item = {
                                 "name": channel_dict["name"],
                                 "id": channel_dict["name"],
                                 "thumbnail": channel_dict["logo"],
                                 }
            channel_list.append(clean_station_item)

        return channel_list

    def get_channel_stream(self, chandict, stream_args):
        streamdict = self.get_channel_dict(self.filtered_chan_list, "name", chandict["origin_name"])
        streamurl = streamdict["url"]

        stream_info = {"url": streamurl}

        return stream_info

    def get_unfiltered_chan_json(self):
        channels = self.plugin_utils.web.session.get(self.channels_json_url).json()
        channel_map = {c['id']: c for c in channels}

        streams = self.plugin_utils.web.session.get(self.streams_json_url).json()
        stream_map = {s['channel']: s for s in streams}

        for s in stream_map:
            if s in channel_map:
                channel_map[s].update(stream_map[s])
        
        return list(channel_map.values())

    def filterlist(self):

        filtered_chan_list = []
        for channels_item in self.unfiltered_chan_list:
            filters_passed = []
            for filter_key in list(self.filter_dict.keys()):

                if not len(self.filter_dict[filter_key]):
                    filters_passed.append(True)
                else:
                    filter_passed = False
                    if filter_key == "countries":
                        if channels_item["country"] in self.filter_dict[filter_key]:
                            filter_passed = True
                    elif filter_key == "category":
                        if self.filter_dict[filter_key] in channels_item["categories"]:
                            filter_passed = True
                    elif filter_key == "languages":
                        if set(self.filter_dict[filter_key]).intersection(set(channels_item[filter_key])):
                            filter_passed = True
                    else:
                        if self.filter_dict[filter_key] == channels_item[filter_key]:
                            filter_passed = True

                    filters_passed.append(filter_passed)

            if False not in filters_passed:
                if channels_item["name"] not in [x["name"] for x in filtered_chan_list]:
                    filtered_chan_list.append(channels_item)

        return filtered_chan_list

    def get_channel_dict(self, chanlist, keyfind, valfind):
        return next(item for item in chanlist if item[keyfind] == valfind) or None
