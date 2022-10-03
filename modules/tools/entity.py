
def call_service_within_entity_domain(entity, service_name, **service_args):
    entity_domain = entity.split(".")[0]
    service.call(entity_domain, service_name, **service_args)
