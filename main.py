#!/usr/bin/env python3

import Scrape_All_UFCStats
import Process_Entire_History

need_to_process = Scrape_All_UFCStats.scrape_stats()
Process_Entire_History.process_jsons_into_csv(need_to_process)