import copy
import multiprocessing
import zmq
import logging
import json

import qsim.util as qutil
import qsim.messaging as qmsg

class TestClient(object):
    
    def __init__(self,feed, address, bind=False):
        self.feed           = feed
        self.address        = address
        self.sync           = qmsg.FeedSync(feed, "testclient")
        self.bind           = bind
        self.received_count = 0
        
    def run(self):
        
        qutil.LOGGER.info("running the client")
        self.context = zmq.Context()
        
        self.data_feed = self.context.socket(zmq.PULL)

        if(self.bind):
            qutil.LOGGER.info("binding to {address}".format(address=self.address))
            self.data_feed.bind(self.address)
        else:
            qutil.LOGGER.info("connecting to {address}".format(address=self.address))
            self.data_feed.connect(self.address)
        
        self.sync.confirm()
        
        qutil.LOGGER.info("Starting the client loop")

        prev_dt = None
        while True:
            msg = self.data_feed.recv()
            if(msg == "DONE"):
                qutil.LOGGER.info("DONE!")
                break
            self.received_count += 1
            event = json.loads(msg)
            if(prev_dt != None):
                if(not event['dt'] >= prev_dt):
                    raise Exception("message arrived out of order: {date} after {prev}".format(date=event['dt'], prev=prev_dt))
            
            prev_dt = event['dt']
            if(self.received_count % 100 == 0):
                qutil.LOGGER.info("received {n} messages".format(n=self.received_count))
            
        qutil.LOGGER.info("received {n} messages".format(n=self.received_count))
        self.data_feed.close()
        self.context.term()