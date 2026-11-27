# IHP SG13G2 power grid. OpenVLSI sources this file during floorplan.
# The layer widths and pitches follow the IHP librelane platform defaults.
# PDN generation is best-effort so very small floorplans still complete.

if {[catch {
    add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^VDD$} -power
    add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {^VSS$} -ground
    global_connect

    set_voltage_domain -name {CORE} -power {VDD} -ground {VSS}

    define_pdn_grid -name {grid} -voltage_domains {CORE}
    add_pdn_stripe -grid {grid} -layer {Metal1} -width {0.44} -pitch {7.56} -offset {0} -followpins
    add_pdn_stripe -grid {grid} -layer {TopMetal1} -width {2.2} -pitch {75.6} -offset {13.6}
    add_pdn_stripe -grid {grid} -layer {TopMetal2} -width {2.2} -pitch {75.6} -offset {13.6}
    add_pdn_connect -grid {grid} -layers {Metal1 TopMetal1}
    add_pdn_connect -grid {grid} -layers {TopMetal1 TopMetal2}

    pdngen
} pdnError]} {
    puts "warning: PDN generation skipped: $pdnError"
}
