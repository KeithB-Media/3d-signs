#!/usr/bin/env bash
# Export every printable part to stl/ and the assembly pictures to renders/.
# Needs OpenSCAD (2021.01 or newer). Pictures need a display: on a headless box
# run it as  xvfb-run ./build.sh
set -e
cd "$(dirname "$0")"
mkdir -p stl/common stl/wall_flat stl/desk_stand stl/wall_projecting renders
o() { echo "  $1"; openscad -q -o "$1" "${@:2}"; }

o stl/common/bezel.stl            -D 'part="bezel"'      wall_flat.scad
o stl/common/led_plate.stl        -D 'part="led_plate"'  wall_flat.scad
o stl/common/blank_face.stl       -D 'part="blank_face"' wall_projecting.scad

o stl/wall_flat/body_wired.stl    -D 'part="body"' -D battery=false wall_flat.scad
o stl/wall_flat/body_battery.stl  -D 'part="body"' -D battery=true  wall_flat.scad

o stl/desk_stand/body.stl           -D 'part="body"'                    desk_stand.scad
o stl/desk_stand/stand_wired.stl    -D 'part="stand"' -D battery=false desk_stand.scad
o stl/desk_stand/stand_battery.stl  -D 'part="stand"' -D battery=true  desk_stand.scad

o stl/wall_projecting/body_a_wired.stl   -D 'part="body_a"' -D battery=false wall_projecting.scad
o stl/wall_projecting/body_a_battery.stl -D 'part="body_a"' -D battery=true  wall_projecting.scad
o stl/wall_projecting/body_b.stl         -D 'part="body_b"'                  wall_projecting.scad
o stl/wall_projecting/arm.stl            -D 'part="arm_print"'                     wall_projecting.scad

# test set (see test/README.md)
mkdir -p test/full_size_fit test/mini
for p in body_arc bezel_arc face_arc; do o test/full_size_fit/$p.stl -D "part=\"$p\"" test_fit.scad; done
for p in body led_plate bezel stand; do o test/mini/$p.stl -D "part=\"$p\"" test_mini.scad; done

if [ "${NO_RENDERS:-}" = "" ]; then
  r() { echo "  $1"; openscad -q --preview --imgsize=1400,1050 --colorscheme=Tomorrow --viewall --autocenter \
          --projection=p -o "$1" "${@:2}"; }
  r test/mini/mini_assembly.png --camera=0,0,0,70,0,-25,0  test_mini.scad
  r test/full_size_fit/fit_parts.png --camera=0,0,0,50,0,20,0 test_fit.scad
  r renders/wall_flat.png        --camera=0,0,0,70,0,-30,0  wall_flat.scad
  r renders/desk_stand.png       --camera=0,0,0,70,0,-25,0  desk_stand.scad
  r renders/wall_projecting.png  --camera=0,0,0,75,0,150,0  wall_projecting.scad
  r renders/wall_projecting_side_a.png --camera=0,0,0,80,0,25,0  wall_projecting.scad
fi
