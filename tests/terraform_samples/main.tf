module "keycloak01-dc1" {
  source                     = "git@gitlab.example.com:example/infra/terraform/pve-vm.git?ref=v1.2.6"
  vm_template                = "ubuntu-2204"
  vm_name                    = "keycloak01-dc1"
  vm_cpu_cores               = "4"
  vm_mem                     = "16384"
  vm_node                    = "pve01-dc1"
  vm_storage                 = "ssd_db01_pve01-dc1"
  dc                         = "dc1"
  vm_pool                    = "app"
  vm_node_domain             = "h.pci-prod.example.local"
  vm_domain                  = "v.pci-prod.example.local"
  vm_disk_size               = "200"
  vlan_id                    = "254"
  vm_desc                    = "INFRA-27842"
  vm_server_role             = "webapp"
  vm_server_maintaining_team = "infra_team"
  vm_server_owning_team      = "infrasec_team"
  vm_server_cluster_name     = "example_pci_stg_keycloak"
  vm_prometheus_env          = "production"
  pdns_server_url            = "http://leader.powerdns.pci-prod.example.local:8081/api/v1/"
  pdns_vault_path            = "infra/examplepci/powerdns/pdns"
  proxmox_vault_path         = "infra/example/proxmox-pci/common"
}

module "keycloak01-dc2" {
  source                     = "git@gitlab.example.com:example/infra/terraform/pve-vm.git?ref=v1.2.6"
  vm_template                = "ubuntu-2204"
  vm_name                    = "keycloak01-dc2"
  vm_cpu_cores               = "4"
  vm_mem                     = "16384"
  vm_node                    = "pve01-dc2"
  vm_storage                 = "ssd_db01_pve01-dc2"
  dc                         = "dc2"
  vm_pool                    = "app"
  vm_node_domain             = "h.pci-prod.example.local"
  vm_domain                  = "v.pci-prod.example.local"
  vm_disk_size               = "200"
  vlan_id                    = "254"
  vm_desc                    = "INFRA-27842"
  vm_server_role             = "webapp"
  vm_server_maintaining_team = "infra_team"
  vm_server_owning_team      = "infrasec_team"
  vm_server_cluster_name     = "example_pci_stg_keycloak"
  vm_prometheus_env          = "production"
  pdns_server_url            = "http://leader.powerdns.pci-prod.example.local:8081/api/v1/"
  pdns_vault_path            = "infra/examplepci/powerdns/pdns"
  proxmox_vault_path         = "infra/example/proxmox-pci/common"
}

module "keycloak01-dc4" {
  source                     = "git@gitlab.example.com:example/infra/terraform/pve-vm.git?ref=v1.2.6"
  vm_template                = "ubuntu-2204"
  vm_name                    = "keycloak01-dc4"
  vm_cpu_cores               = "4"
  vm_mem                     = "16384"
  vm_node                    = "pve01-dc4"
  vm_storage                 = "ssd_db01_pve01-dc4"
  dc                         = "dc4"
  vm_pool                    = "app"
  vm_node_domain             = "h.pci-prod.example.local"
  vm_domain                  = "v.pci-prod.example.local"
  vm_disk_size               = "200"
  vlan_id                    = "254"
  vm_desc                    = "INFRA-27842"
  vm_server_role             = "webapp"
  vm_server_maintaining_team = "infra_team"
  vm_server_owning_team      = "infrasec_team"
  vm_server_cluster_name     = "example_pci_stg_keycloak"
  vm_prometheus_env          = "production"
  pdns_server_url            = "http://leader.powerdns.pci-prod.example.local:8081/api/v1/"
  pdns_vault_path            = "infra/examplepci/powerdns/pdns"
  proxmox_vault_path         = "infra/example/proxmox-pci/common"
}