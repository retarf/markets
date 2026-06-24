from airflow.sdk import dag, task, Asset, AssetAlias, get_current_context


test_alias = AssetAlias("test_alias")


@dag
def producer_dag():

    @task(outlets=[test_alias])
    def emit_asset(num, *, outlet_events):
        ds = get_current_context()["ds"]
        outlet_events[test_alias].add( Asset(f"file:///datalake/{ ds }/{ num }/new.csv") )
    
    @task
    def dummy_task():
        print("Dummy Task I")

    emmit = emit_asset.expand(num=[1, 2, 3])
    dummy = dummy_task()


@dag(schedule=[test_alias])
def consumer_dag():

    @task(inlets=[test_alias])
    def consume_asset(*, inlet_events):
        events = inlet_events[test_alias]
        for ev in events:
            print(ev)
    
    consume_asset()


producer = producer_dag()
consumer = consumer_dag()

