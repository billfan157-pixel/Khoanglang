"""Correct the duplicated entrance frames and open leaves in the primary copy."""
import unreal
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if editor.get_game_world(): raise RuntimeError('Stop PIE first')
world=editor.get_editor_world()
if '/Production/Maps/Lvl_KL_School3_Primary' not in world.get_path_name(): raise RuntimeError('Primary map required')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
labels={a.get_actor_label():a for a in actors.get_all_level_actors()}
frame=labels['ART_DoorEntry_FrameW']
frame.modify()
frame.set_actor_location(unreal.Vector(-400,0,0),False,False)
frame.set_actor_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0),False)
frame.set_actor_scale3d(unreal.Vector(1.55,1,1))
if 'ART_DoorEntry_FrameE' in labels: actors.destroy_actor(labels['ART_DoorEntry_FrameE'])
for name,y in [('ART_DoorEntry_LeafN',115),('ART_DoorEntry_LeafS',-115)]:
    a=labels[name]; a.modify()
    a.set_actor_location(unreal.Vector(-350,y,1),False,False)
    a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0),False)
classroom_leaf=labels['ART_Door3_Leaf']
classroom_leaf.modify()
classroom_leaf.set_actor_location(unreal.Vector(800,220,1),False,False)
classroom_leaf.set_actor_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0),False)
world.modify()
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(): raise RuntimeError('Entry save failed')
print('PRIMARY_ENTRY_REPAIRED')
