-- Quote-to-Provision Assistant: Supabase (PostgreSQL) schema.
-- Idempotent: safe to run more than once. Run in the Supabase SQL Editor,
-- or with `python apply_schema.py` when DATABASE_URL is set in backend/.env.

-- ---------------------------------------------------------------------------
-- Reference data (curated JSON sources)
-- ---------------------------------------------------------------------------

create table if not exists product_catalog (
    product_id          text primary key,
    name                text not null,
    product_type        text not null,
    description         text,
    bandwidth_value     numeric,
    bandwidth_unit      text,
    bandwidth_symmetry  text,
    latency_ms          numeric,
    sla_uptime          numeric,
    setup_cost          numeric(14, 2),
    monthly_cost        numeric(14, 2),
    lead_time_days      integer,
    currency            text not null default 'USD',
    features            jsonb not null default '[]',
    extra               jsonb not null default '{}',
    source              text not null check (source in ('mock', 'real')),
    data_quality_label  text,
    created_at          timestamptz not null default now()
);
create index if not exists idx_product_catalog_type on product_catalog (product_type);

create table if not exists locations (
    site_id                   text primary key,
    name                      text not null,
    address                   text,
    region                    text,
    data_center_tier          text,
    latitude                  numeric,
    longitude                 numeric,
    rack_units                integer,
    available_rack_units      integer,
    power_capacity_kw         numeric,
    available_power_kw        numeric,
    cooling_capacity_kw       numeric,
    available_cooling_kw      numeric,
    aws_direct_connect        boolean,
    aws_available_ports       integer,
    azure_expressroute        boolean,
    azure_available_circuits  integer,
    gcp_interconnect          boolean,
    internet_uplink_gbps      numeric,
    metro_ethernet_ports      integer,
    mpls_vpn_capacity         text,
    dark_fiber_strands        integer,
    inventory_last_updated    date,
    extra                     jsonb not null default '{}',
    source                    text not null check (source in ('mock', 'real')),
    data_quality_label        text,
    created_at                timestamptz not null default now()
);
create index if not exists idx_locations_region on locations (region);

create table if not exists past_projects (
    project_id            text primary key,
    name                  text not null,
    description           text,
    client                text,
    location              text,
    region                text,
    primary_bandwidth     numeric,
    secondary_bandwidth   numeric,
    bandwidth_unit        text,
    cloud_platforms       jsonb not null default '[]',
    cloud_distribution    jsonb not null default '{}',
    sla_uptime_pct        numeric,
    sla_response_time_ms  numeric,
    sla_support_level     text,
    start_date            date,
    completion_date       date,
    duration_months       integer,
    total_cost            numeric(14, 2),
    setup_cost            numeric(14, 2),
    monthly_operational   numeric(14, 2),
    currency              text not null default 'USD',
    lessons_learned       jsonb not null default '[]',
    extra                 jsonb not null default '{}',
    source                text not null check (source in ('synthetic', 'real')),
    data_quality_label    text,
    created_date          date
);
create index if not exists idx_past_projects_region on past_projects (region);

create table if not exists mcgw_pricing (
    id               bigint generated always as identity primary key,
    source_file      text not null,
    source_row       integer not null,
    source_id        text,
    component_id     text,
    component_type   text,
    description      text,
    hourly_rate      numeric,
    monthly_rate     numeric,
    category         text,
    class_of_service text,
    unique (source_file, source_row)
);

-- ---------------------------------------------------------------------------
-- Operational data (Excel exports of Lumen systems)
-- Bandwidth columns are stored as reported by the source system.
-- ---------------------------------------------------------------------------

create table if not exists uni_sites (
    id                  bigint generated always as identity primary key,
    source_file         text not null,
    source_row          integer not null,
    source_id           text,
    name                text,
    uni_service_id      text,
    uni_type            text,
    status              text,
    network_type        text,
    ring_type           text,
    ring_id             text,
    billing_account_number text,
    location_id         text,
    service_address     text,
    latitude            numeric,
    longitude           numeric,
    site_id             text,
    created_at_source   timestamptz,
    device_name         text,
    device_port         text,
    device_port_speed   numeric,
    device_model        text,
    device_vendor       text,
    device_role_code    text,
    pe_device_name      text,
    pe_device_port      text,
    pe_device_model     text,
    pe_device_vendor    text,
    pe_device_role_code text,
    customer_name       text,
    customer_bus_org_id text,
    customer_ban        text,
    details             jsonb not null default '{}',
    unique (source_file, source_row)
);
create index if not exists idx_uni_sites_uni_service_id on uni_sites (uni_service_id);
create index if not exists idx_uni_sites_site_id on uni_sites (site_id);
create index if not exists idx_uni_sites_status on uni_sites (status, network_type);

create table if not exists customer_ports (
    id              bigint generated always as identity primary key,
    source_file     text not null,
    source_row      integer not null,
    source_id       text,
    uni_service_id  text,
    status          text,
    customer_ban    text,
    unique (source_file, source_row)
);
create index if not exists idx_customer_ports_uni on customer_ports (uni_service_id);

create table if not exists whitelisted_ports (
    id                          bigint generated always as identity primary key,
    source_file                 text not null,
    source_row                  integer not null,
    name                        text,
    billing_account_number      text,
    uni_type                    text,
    uni_service_id              text,
    status                      text,
    network_type                text,
    ring_type                   text,
    ring_id                     text,
    location_id                 text,
    service_address             text,
    site_id                     text,
    device_name                 text,
    device_port                 text,
    device_port_speed           numeric,
    device_model                text,
    device_network              text,
    device_vendor               text,
    device_role_code            text,
    device_wan_port             text,
    mc_device_1                 text,
    mc_device_2                 text,
    agg_device_name             text,
    agg_device_port             text,
    pe_device_name              text,
    pe_device_port              text,
    pe_device_port_speed        numeric,
    pe_device_role_code         text,
    pe_device_model             text,
    pe_device_network           text,
    pe_device_vendor            text,
    port_product_instance_id    text,
    customer_name               text,
    customer_bus_org_id         text,
    customer_ban                text,
    customer_eid                text,
    customer_invoice_display_ban text,
    unique (source_file, source_row)
);
create index if not exists idx_whitelisted_ports_uni on whitelisted_ports (uni_service_id);
create index if not exists idx_whitelisted_ports_site on whitelisted_ports (site_id);
create index if not exists idx_whitelisted_ports_pe on whitelisted_ports (pe_device_name);

create table if not exists evcs (
    id                        bigint generated always as identity primary key,
    source_file               text not null,
    source_row                integer not null,
    evc_id                    text,
    evc_name                  text,
    bandwidth                 numeric,
    billing_type              text,
    charge_type               text,
    billing_bandwidth         numeric,
    cos                       text,
    billing_cos               text,
    billing_account_number    text,
    endpoint1_uni_service_id  text,
    endpoint2_uni_service_id  text,
    customer_bus_org_id       text,
    monthly_rate              numeric,
    detail                    text,
    unique (source_file, source_row)
);
create index if not exists idx_evcs_evc_id on evcs (evc_id);
create index if not exists idx_evcs_ep1 on evcs (endpoint1_uni_service_id);
create index if not exists idx_evcs_ep2 on evcs (endpoint2_uni_service_id);

create table if not exists provisioning_requests (
    id                  bigint generated always as identity primary key,
    source_file         text not null,
    source_row          integer not null,
    source_id           text,
    product_family      text not null check (product_family in ('edge_ipvpn', 'edge_internet', 'dycon_ipvpn')),
    request_id          text,
    resource_id         text,
    account_id          text,
    customer_name       text,
    friendly_name       text,
    status              text,
    operation           text,
    state               text,
    product_type        text,
    message             text,
    clli_code           text,
    service_id          text,
    vrf_name            text,
    ip_block            text,
    bandwidth           numeric,
    monthly_rate        numeric,
    timeout_seconds     integer,
    build_start_time    timestamptz,
    build_finish_time   timestamptz,
    modify_start_time   timestamptz,
    modify_finish_time  timestamptz,
    delete_start_time   timestamptz,
    delete_finish_time  timestamptz,
    source_created_at   timestamptz,
    source_deleted_at   timestamptz,
    details             jsonb not null default '{}',
    unique (source_file, source_row)
);
create index if not exists idx_prov_req_family on provisioning_requests (product_family, status, operation);
create index if not exists idx_prov_req_request_id on provisioning_requests (request_id);
create index if not exists idx_prov_req_account on provisioning_requests (account_id);
create index if not exists idx_prov_req_service_id on provisioning_requests (service_id);

create table if not exists service_order_failures (
    id              bigint generated always as identity primary key,
    source_file     text not null,
    source_row      integer not null,
    source_id       text,
    service_family  text not null,
    request_id      text,
    account_id      text,
    evc_id          text,
    bandwidth       numeric,
    status          text,
    operation       text,
    message         text,
    unique (source_file, source_row)
);
create index if not exists idx_failures_family on service_order_failures (service_family, operation);
create index if not exists idx_failures_account on service_order_failures (account_id);

create table if not exists inventory_dq_issues (
    id              bigint generated always as identity primary key,
    source_file     text not null,
    source_row      integer not null,
    uni_service_id  text,
    customer_ban    text,
    issue_count     integer not null default 0,
    issues          jsonb not null default '[]',
    details         jsonb not null default '{}',
    unique (source_file, source_row)
);
create index if not exists idx_inventory_dq_uni on inventory_dq_issues (uni_service_id);

-- ---------------------------------------------------------------------------
-- Application output: proposals / provisioning orders produced by the assistant
-- (mirrors schemas/provisioning_schema.json)
-- ---------------------------------------------------------------------------

create table if not exists provisioning_orders (
    provisioning_id         text primary key,
    customer_id             text,
    customer_name           text,
    project_name            text,
    status                  text not null default 'draft'
                            check (status in ('draft', 'submitted', 'approved', 'in_progress', 'completed', 'cancelled')),
    architecture_type       text,
    primary_site_id         text references locations (site_id),
    total_sites             integer,
    total_bandwidth_value   numeric,
    total_bandwidth_unit    text,
    redundancy_model        text,
    implementation_model    text,
    planned_start_date      date,
    planned_completion_date date,
    total_setup_cost        numeric(14, 2),
    total_monthly_cost      numeric(14, 2),
    currency                text not null default 'USD',
    payload                 jsonb not null default '{}',
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now()
);
create index if not exists idx_prov_orders_status on provisioning_orders (status);

create table if not exists bom_items (
    id                    bigint generated always as identity primary key,
    provisioning_id       text not null references provisioning_orders (provisioning_id) on delete cascade,
    line_item_id          text not null,
    product_id            text not null references product_catalog (product_id),
    quantity              integer not null default 1,
    unit_of_measure       text,
    unit_setup_cost       numeric(14, 2),
    unit_monthly_cost     numeric(14, 2),
    discount_percent      numeric default 0,
    customization_config  jsonb not null default '{}',
    unique (provisioning_id, line_item_id)
);

create table if not exists site_allocations (
    id                bigint generated always as identity primary key,
    bom_item_id       bigint not null references bom_items (id) on delete cascade,
    site_id           text not null references locations (site_id),
    quantity_at_site  integer not null default 1,
    deployment_role   text check (deployment_role in ('primary', 'secondary', 'backup', 'distributed')),
    rack_location     text,
    port_assignment   jsonb not null default '{}'
);

-- ---------------------------------------------------------------------------
-- Row Level Security.
-- The operational tables hold real customer names, BANs and addresses.
-- With RLS enabled and no policies, the publishable (anon) key can read nothing;
-- the backend uses the secret key, which bypasses RLS and must stay server-side.
-- ---------------------------------------------------------------------------

alter table product_catalog         enable row level security;
alter table locations               enable row level security;
alter table past_projects           enable row level security;
alter table mcgw_pricing            enable row level security;
alter table uni_sites               enable row level security;
alter table customer_ports          enable row level security;
alter table whitelisted_ports       enable row level security;
alter table evcs                    enable row level security;
alter table provisioning_requests   enable row level security;
alter table service_order_failures  enable row level security;
alter table inventory_dq_issues     enable row level security;
alter table provisioning_orders     enable row level security;
alter table bom_items               enable row level security;
alter table site_allocations        enable row level security;

notify pgrst, 'reload schema';
