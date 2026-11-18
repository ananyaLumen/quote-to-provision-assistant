# Network Schema and Provisioning Architecture

**Date:** 2024-11-18  
**Version:** 1.0  
**Status:** Ready for Integration  

---

## Overview

This document defines the network product attributes, provisioning structure, and Bill of Materials (BOM) format for the Quote-to-Provision Assistant. The schemas enable consistent representation of network solutions, pricing, and deployment logistics across all system components.

### Key Components

1. **network_schema.json** — Comprehensive product definition format
2. **provisioning_schema.json** — Order structure for provisioning and implementation
3. **sample_provisioning_payload.json** — Illustrative real-world example

---

## 1. Network Schema (network_schema.json)

### Purpose

Defines the complete attribute set for network products in the catalog. Used for:
- Product catalog storage and retrieval
- Matching products to customer requirements
- Technical specification validation
- Cost and lead time estimation

### Structure

The schema is organized into 8 major sections:

#### 1.1 Metadata
- **schema_version**: Semantic version (e.g., "1.0")
- **schema_date**: Date schema was finalized

#### 1.2 Product Attributes
Core identification and classification:
- **product_id**: Unique identifier (NP-TYPE-NNN format)
- **product_name**: Human-readable name
- **product_type**: Category (connectivity, security, load_balancing, etc.)
- **product_category**: Functional role (transport, access, threat_prevention, etc.)
- **product_tier**: Market segment (enterprise, mid-market, smb, edge)

#### 1.3 Technical Specifications
Performance and capability characteristics:
- **bandwidth**: Value, unit (Mbps/Gbps/Tbps), symmetry (symmetric/asymmetric/burstable)
- **latency_ms**: End-to-end latency
- **throughput_tps**: Transactions/connections per second
- **packet_loss**: Acceptable loss percentage
- **jitter_ms**: Maximum acceptable jitter
- **supported_protocols**: BGP, OSPF, MPLS, HTTP/2, QUIC, etc.
- **supported_standards**: IEEE, RFC, FIPS, etc.

#### 1.4 Service Level Requirements
SLA and support characteristics:
- **uptime_percentage**: Guaranteed uptime (90-99.999)
- **response_time_ms**: Maximum acceptable response time
- **recovery_time_objective_min**: RTO (minutes)
- **recovery_point_objective_min**: RPO (minutes)
- **support_model**: 24/7/365, 24/7, business_hours, on_demand
- **support_response_sla_hours**: Hours to first response
- **maintenance_window_hours**: Maximum maintenance duration

#### 1.5 Pricing Model
Financial attributes:
- **setup_cost_usd**: One-time implementation cost
- **monthly_cost_usd**: Recurring monthly cost
- **cost_per_unit**: Alternative pricing (per Gbps, per port, per transaction, per user)
- **contract_term_months**: Minimum commitment (1, 12, 24, 36)
- **discounts_available**: Boolean flag for volume/commitment discounts
- **currency**: Currency code (default: USD)

#### 1.6 Deployment Logistics
Implementation and physical requirements:
- **lead_time_days**: Days from order to deployment-ready
- **implementation_days**: Typical implementation duration
- **installation_complexity**: simple/moderate/complex
- **equipment_weight_kg**: Physical weight
- **rack_units_required**: Space requirement (1U units)
- **power_consumption_watts**: Maximum power draw
- **cooling_requirement_watts**: Heat dissipation

#### 1.7 Compatibility
Ecosystem and platform integration:
- **compatible_platforms**: AWS, Azure, GCP, On-Premises
- **compatible_products**: Product IDs this integrates with
- **api_available**: Boolean flag for REST/GraphQL API
- **api_version**: Available versions (v1, v2, v3)
- **orchestration_support**: Terraform, Ansible, CloudFormation, ARM
- **licensing_model**: perpetual, subscription, pay-as-you-go, free

#### 1.8 Compliance & Security
Security posture and certifications:
- **certifications**: ISO 27001, SOC 2 Type II, HIPAA, PCI-DSS, GDPR
- **encryption_support**: AES-256, TLS 1.3, ChaCha20
- **data_residency_options**: US-East, EU, APAC, GovCloud
- **audit_logging**: Boolean flag for detailed audit capability
- **threat_intelligence**: Boolean flag for threat feeds

#### 1.9 Feature Set
Detailed capabilities:
- **core_features**: Essential product capabilities (minimum 1)
- **advanced_features**: Optional premium features
- **automation_capabilities**: Auto-failover, Self-healing, Auto-scaling
- **monitoring_telemetry**: NetFlow, sFlow, SNMP, Prometheus, CloudWatch

### Product Type Mapping

| Type | Category | Use Case | Example |
|------|----------|----------|---------|
| connectivity | transport, access | Network transport services | Metro Ethernet, MPLS VPN, Cloud Direct Connect |
| security | threat_prevention | Security and protection | Firewall, WAF, DLP |
| load_balancing | performance | Traffic distribution | L4/L7 load balancer |
| wan_optimization | performance | WAN acceleration | WAN optimizer, SD-WAN |
| monitoring | orchestration | Operational visibility | Digital Experience Platform |
| management | orchestration | Infrastructure management | IPAM, orchestration platform |
| services | consulting | Professional services | Network design, implementation |

---

## 2. Provisioning Schema (provisioning_schema.json)

### Purpose

Defines the complete provisioning order structure for network solution deployment. Used for:
- Order submission and tracking
- Bill of Materials (BOM) creation
- Site allocation and resource planning
- Cost estimation and approval workflows
- Implementation tracking

### Structure

The schema consists of 10 major sections:

#### 2.1 Metadata Fields
- **provisioning_id**: Unique order identifier (PROV-YYYY-XXXXXX)
- **provisioning_date**: Order creation date
- **status**: Current state (draft, submitted, approved, in_progress, completed, cancelled)

#### 2.2 Customer Information
- **customer_id**: Customer unique identifier
- **customer_name**: Organization name
- **customer_contact**: Email, phone, primary contact
- **project_name**: Associated project name
- **project_id**: Reference to customer project

#### 2.3 Deployment Schedule
Timeline and phases:
- **planned_start_date**: Deployment start
- **planned_completion_date**: Target completion
- **deployment_phases**: Array of phased rollout stages
  - phase_number, phase_name, description, start_date, end_date, affected_sites
- **maintenance_windows**: Scheduled maintenance windows during deployment

#### 2.4 Bill of Materials (BOM)
Core operational structure — array of line items:

**Each BOM item contains:**
- **line_item_id**: Unique within order (BOM-0001 format)
- **product_id**: Reference to network product catalog
- **product_name**: Product name for reference
- **product_type**: Product category
- **quantity**: Number of units
- **unit_of_measure**: units, circuits, ports, licences, hours, sites
- **site_allocation**: Array of site placements
  - site_id, site_name, quantity_at_site, deployment_role (primary/secondary/backup/distributed)
  - rack_location, port_assignment (interface_type, interface_id, vlan_id)
- **customization_config**: Product-specific parameters (additionalProperties allowed)
- **pricing**: Cost breakdown per line item
  - unit_setup_cost, unit_monthly_cost, total_setup_cost, total_monthly_cost
  - discount_percent, currency

#### 2.5 Network Architecture
High-level topology design:
- **architecture_type**: hub_spoke, mesh, ring, hybrid
- **primary_site**: Hub site reference
- **regions_covered**: Geographic regions (North America, Europe, Asia-Pacific, etc.)
- **total_sites**: Count of sites in provisioning
- **total_bandwidth**: Aggregate capacity (value, unit)
- **redundancy_model**: none, active_passive, active_active, n+1, n+2
- **cloud_integration**: Cloud providers, direct_connect requirement, hybrid_cloud flag

#### 2.6 Implementation Details
Deployment approach and logistics:
- **implementation_model**: waterfall, agile, phased, big_bang
- **implementation_partner**: Partner organization and contact info
- **testing_requirements**: Pre-production, load, security, failover, UAT flags
- **training_requirements**: Operator/admin/escalation hours, format (on_site/remote/documentation)
- **documentation_deliverables**: Array of required documentation (design, runbook, DR plan, etc.)

#### 2.7 Cost Summary
Financial aggregation across all BOM items:
- **total_setup_cost**: Sum of all one-time costs
- **total_monthly_cost**: Sum of all recurring costs
- **first_year_total**: Setup + (12 × monthly)
- **three_year_tco**: Setup + (36 × monthly)
- **discounts_applied**: Total discount amount
- **currency**: Currency code

#### 2.8 Approval Workflow
Sign-off chain:
- **technical_approval**: Approver, approval_date, comments
- **financial_approval**: Approver, approval_date, budget_code
- **customer_acceptance**: Customer signoff, signoff_date

#### 2.9 Attachments
Associated documents and references:
- **network_diagram_url**: Topology diagram link
- **proposal_id**: Reference to proposal
- **quote_id**: Reference to quote
- **supporting_documents**: Array of attachments (name, type, URL)

#### 2.10 Data Quality Label
- **data_quality_label**: REAL, MOCK, or SYNTHETIC

---

## 3. Bill of Materials (BOM) Structure

### Definition

The BOM is the operational core of a provisioning order. It represents the specific products, quantities, sites, and costs that compose a network solution.

### Key Principles

**Line Item Composition:**
- Each line item maps one product to one or more deployment sites
- Site allocation specifies quantities and roles (primary/secondary/backup)
- Customization allows product-specific configuration parameters
- Pricing is calculated per line item and aggregated into cost summary

**Site Allocation:**
- Specifies which sites receive which products and in what quantity
- Deployment role defines functional position:
  - **primary**: Active, production role
  - **secondary**: Active, backup/distributed role
  - **backup**: Standby for failover
  - **distributed**: Deployed across multiple sites
- Rack location indicates physical placement
- Port assignment specifies network interface and VLAN tagging

**Pricing Logic:**
- unit_setup_cost = per-unit one-time cost
- unit_monthly_cost = per-unit recurring cost
- total_setup_cost = unit_setup_cost × quantity
- total_monthly_cost = unit_monthly_cost × quantity
- Discount applied proportionally to both setup and monthly costs

### Example BOM Item (Connectivity)

```json
{
  "line_item_id": "BOM-0001",
  "product_id": "NP-CONN-002",
  "product_name": "[MOCK] Cloud Interconnect AWS 100G",
  "product_type": "connectivity",
  "quantity": 2,
  "unit_of_measure": "circuits",
  "site_allocation": [
    {
      "site_id": "SITE-010",
      "site_name": "[MOCK] Los Angeles - West Coast",
      "quantity_at_site": 2,
      "deployment_role": "primary",
      "rack_location": "Rack-B-18",
      "port_assignment": {
        "interface_type": "AWS Direct Connect",
        "interface_id": "dxcon-0a1b2c3d",
        "vlan_id": 101
      }
    }
  ],
  "customization_config": {
    "connection_speed": "100Gbps",
    "enable_bfd": true,
    "mtu_size": 1500
  },
  "pricing": {
    "unit_setup_cost": 45000,
    "unit_monthly_cost": 18000,
    "total_setup_cost": 90000,
    "total_monthly_cost": 36000,
    "discount_percent": 10,
    "currency": "USD"
  }
}
```

---

## 4. Sample Provisioning Payload

### Overview

The [sample_provisioning_payload.json](sample_provisioning_payload.json) illustrates a complete, real-world provisioning order for a retail company upgrading their Los Angeles data center infrastructure.

### Key Features Demonstrated

**Customer Context:**
- Real customer information with contact details
- Associated project (West Coast Regional Network Upgrade)

**Multi-Phase Deployment:**
- Phase 1: Hub installation (Dec 15 - Jan 15)
- Phase 2: Secondary site (Jan 16 - Feb 15)
- Phase 3: Testing & optimization (Feb 16 - Feb 28)
- Scheduled maintenance windows for minimal impact

**Complete BOM:**
- 2× AWS Direct Connect circuits (100G each) — connectivity
- 1× Enterprise Security Gateway (40G) — threat prevention
- 1× Enterprise Load Balancer (100G) — traffic management
- 1× Web Application Firewall (50G) — application security
- 1× Digital Experience Platform — monitoring
- 60 hours of professional services — consulting

**Network Architecture:**
- Hub-spoke topology with Los Angeles as hub
- Active-active redundancy model
- 100 Gbps aggregate bandwidth
- AWS cloud integration via Direct Connect

**Financial Summary:**
- **Setup:** $210,000 (after $15,000 discount)
- **Monthly:** $59,000
- **Year 1:** $918,000
- **3-Year TCO:** $2,334,000

**Approval Chain:**
- Technical approval (VP Infrastructure) — alignment with multi-cloud strategy
- Financial approval (CFO) — budget allocation and codes
- Customer acceptance (Network Director) — sign-off on design and timeline

---

## 5. Field Naming Conventions

### Consistency Across Datasets

All three datasets (past_projects.json, product_catalog.json, inventory.json) and schemas use aligned field names for interoperability:

| Concept | Field Name | Type | Used In |
|---------|-----------|------|---------|
| Geographic location | location | string | Projects, Inventory, Provisioning |
| Geographic region | region | string | Projects, Inventory |
| Cloud provider | cloud_platforms | array | Projects, Inventory, Provisioning |
| Bandwidth | bandwidth | object or string | Products, Projects, Inventory, Provisioning |
| SLA uptime | sla_uptime | number OR sla.uptime_percentage | Products vs Projects (harmonized) |
| Response time | response_time_ms | number | Products, SLA specifications |
| Setup cost | setup_cost / setup_cost_usd | number | Products, BOM line items |
| Monthly cost | monthly_cost / monthly_cost_usd | number | Products, BOM line items |
| Lead time | lead_time_days | number | Products |
| Data quality | data_quality_label | string | All datasets |
| Site reference | site_id | string | Inventory, Provisioning (BOM allocation) |

### Naming Standards

- **Date fields**: ISO 8601 format (YYYY-MM-DD)
- **Time fields**: 24-hour format (HH:MM)
- **Cost fields**: Numeric, suffix with _usd for clarity where ambiguous
- **Boolean fields**: lowercase true/false
- **IDs**: Uppercase, hyphen-separated format (e.g., SITE-001, NP-CONN-002)
- **Arrays**: Lowercase plural nouns (features, cloud_platforms, site_allocation)
- **Objects**: Lowercase snake_case (bandwidth, cloud_onramp, cost_summary)

---

## 6. Validation Rules

### Network Schema Validation

1. **Product ID Format**: Must match ^NP-[A-Z]+-[0-9]{3}$
   - Type must be valid category (connectivity, security, etc.)
   - Number must be sequential within type

2. **Technical Specifications Consistency**:
   - If sla_uptime ≥ 99.99, then latency_ms ≤ 10
   - If symmetry is "symmetric", upload ≈ download
   - latency_ms must be < 1000 (reasonable network bounds)

3. **Pricing Consistency**:
   - All costs must be non-negative
   - If monthly_cost = 0, it's a one-time service
   - setup_cost typically > monthly_cost × 2 for products

4. **Lead Time Alignment**:
   - Service products: 7-15 days (catalog/off-shelf)
   - Standard products: 15-30 days
   - Custom interconnects: 30-60 days
   - installation_complexity must align with lead_time

### Provisioning Schema Validation

1. **Date Sequence**:
   - provisioning_date ≤ planned_start_date ≤ planned_completion_date
   - Each phase: start_date < end_date
   - Phases should not overlap

2. **BOM Consistency**:
   - line_item_id must be unique within provisioning
   - quantity > 0 for all items
   - site_allocation quantities must sum to total quantity
   - product_id must exist in product catalog

3. **Cost Calculation**:
   - line_item total_setup_cost = unit_setup_cost × quantity
   - line_item total_monthly_cost = unit_monthly_cost × quantity
   - provisioning total_setup_cost = sum of all line item setup costs
   - first_year_total = total_setup_cost + (12 × total_monthly_cost)
   - three_year_tco = total_setup_cost + (36 × total_monthly_cost)

4. **Site Allocation**:
   - site_id must exist in inventory
   - deployment_role must be valid (primary, secondary, backup, distributed)
   - For hub_spoke architecture, primary_site should appear in BOM allocations

---

## 7. Integration Points

### Data Flow

```
Past Projects (RAG)
    ↓
Customer Requirements
    ↓
Product Catalog Matching
    ↓
Inventory Site Selection
    ↓
BOM Composition
    ↓
Provisioning Order
    ↓
Cost Summary & Approval
```

### API Endpoints (Recommended)

- `GET /api/v1/products/{product_id}` — Fetch single product schema
- `GET /api/v1/products?type=connectivity` — Filter products by type
- `GET /api/v1/inventory/sites` — List available sites
- `GET /api/v1/inventory/sites/{site_id}` — Site capacity details
- `POST /api/v1/provisioning` — Create provisioning order
- `GET /api/v1/provisioning/{prov_id}` — Retrieve provisioning details
- `PUT /api/v1/provisioning/{prov_id}` — Update provisioning order
- `GET /api/v1/provisioning/{prov_id}/cost-summary` — Cost breakdown

---

## 8. Version History & Evolution

### Version 1.0 (2024-11-18) — Initial Release

**Network Schema:**
- Complete product definition structure
- 8 major sections covering technical, commercial, and operational aspects
- Support for all network product categories

**Provisioning Schema:**
- BOM-centric provisioning order structure
- Multi-phase deployment support
- Approval workflow integration

**Datasets:**
- 8 synthetic past projects
- 15 mock network products
- 10 mock site inventory records

**Future Enhancements (v1.1+):**
- Support for multi-vendor orchestration templates
- GraphQL schema variants
- Real-time capacity tracking
- SLA breach prediction models
- Automated BOM optimization suggestions

---

## 9. Document & Reference Standards

### Field Descriptions
Every field includes:
- Type specification
- Required/optional designation
- Description of purpose and usage
- Examples where applicable

### Code Consistency
All examples use:
- ISO 8601 dates
- Proper JSON formatting (2-space indentation)
- Real-world-inspired values
- Clear labeling ([MOCK], [SYNTHETIC]) for test data

### Schema Conformance
- JSON Schema Draft 7 compatibility
- Strict validation rules
- No arbitrary additional properties
- Clear error messages for failures

---

## 10. Getting Started

### Quick Start: Creating a Provisioning Order

1. **Define Customer & Project**
   ```json
   "customer_info": { ... },
   "project_name": "...",
   "deployment_schedule": { ... }
   ```

2. **Build Bill of Materials**
   - Query product_catalog.json for relevant products
   - Create BOM line items with site allocation
   - Calculate costs based on quantities and locations

3. **Allocate Sites**
   - Query inventory.json for available capacity
   - Verify power, cooling, rack space availability
   - Confirm cloud onramp connectivity

4. **Define Network Architecture**
   - Choose topology: hub_spoke, mesh, ring, hybrid
   - Set redundancy model based on SLA
   - Specify cloud integration requirements

5. **Estimate Costs**
   - Sum all line item costs
   - Apply volume discounts if applicable
   - Calculate 1-year and 3-year TCO

6. **Obtain Approvals**
   - Technical: Align with architecture standards
   - Financial: Verify budget allocation
   - Customer: Confirm timeline and deliverables

---

**Last Updated:** 2024-11-18  
**Prepared By:** Member 4 — Network Solution Engineer  
**Status:** Ready for Production Integration  

For questions, refer to [DATA_DOCUMENTATION.md](../data/DATA_DOCUMENTATION.md) for field definitions or contact the network engineering team.
