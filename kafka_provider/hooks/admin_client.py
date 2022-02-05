import functools
from typing import Any, Dict, Optional, Sequence, List

from confluent_kafka.admin import AdminClient, NewTopic

from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook



def client_required(method):
    def inner(ref,*args,**kwargs):
        if not ref.admin_client:
            ref.get_admin_client()
        return method(ref,*args,**kwargs)
    return inner


class AdminClientHook(BaseHook):
    """
    A hook to create a Kafka Producer
    """

    default_conn_name = 'kafka_default'

    def __init__(
        self,
        kafka_conn_id: Optional[str] = None,
        config: Optional[Dict[Any,Any]] = None
    ) -> None:
        super().__init__()

        self.kafka_conn_id = kafka_conn_id
        self.config = config
        self.admin_client = None

        if not (config.get('bootstrap.servers',None) or self.kafka_conn_id ):
            raise AirflowException(f"One of config['bootsrap.servers'] or kafka_conn_id must be provided.")

        if config.get('bootstrap.servers',None) and self.kafka_conn_id :
            raise AirflowException(f"One of config['bootsrap.servers'] or kafka_conn_id must be provided.")
        


    def get_admin_client(self) -> None:
        """
        Returns http session to use with requests.

        :param headers: additional headers to be passed through as a dictionary
        :type headers: dict
        """
        extra_configs = {}
        if self.kafka_conn_id:
            conn = self.get_connection(self.kafka_conn_id)
            extra_configs = {'bootstrap.servers':conn}
    
        self.admin_client = AdminClient({**self.config,**extra_configs})
        return


    @client_required
    def create_topic(self,
            topics: Sequence[Sequence[Any]],
            ) -> None:

        new_topics = [ NewTopic(t[0],num_partitions=t[1],replication_factor=t[2]) for t in topics]
        
        futures = self.admin_client.create_topics(new_topics)

        for t,f in futures.items():
            try:
                f.result()
                self.log.info(f"The topic {t} has been created.")
            except Exception as e:
                if e.args[0].name() == 'TOPIC_ALREADY_EXISTS':
                    self.log.warning(f"The topic {t} already exists.")
                    pass



        

                    


        

