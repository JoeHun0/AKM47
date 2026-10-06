#!/bin/sh
# Render all AKM-47 icon layers into model_export/icons (cameras fitted to the AKM-74S vanilla icons).
# Output path must be absolute: Blender resolved a relative one against C:\ (files ended in C:\model_export).
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
O="$(cd ../.. && pwd -W)/model_export/icons"; mkdir -p "$O"
EXP=${EXP:--2.5}
R() { "$BL" -b -P blender_render_icon.py -- akm47 "$@" --engine CYCLES --samples 128 --exposure $EXP 2>&1 | grep -E "RENDERED|Error|Trace"; }
R body     cam_inv.json "$O/T_inv_w_akm47_body.png" --left
R mag      cam_inv.json "$O/T_inv_w_akm47_defaultmag.png" --left --holdout body
R body     cam_upg.json "$O/T_inv_w_akm47_body_upgrade.png"
R mag      cam_upg.json "$O/T_inv_w_akm47_defaultmag_upgrade.png" --holdout body
R body+mag cam_pda.json "$O/T_pda_statistic_weapon_akm47.png"
