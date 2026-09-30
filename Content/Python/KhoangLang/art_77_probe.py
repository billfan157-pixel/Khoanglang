"""Art pass probe 77: which screenshot API exists, and does it need a viewport?

Screenshots are the only way to honestly judge the art pass, so the API has to
be pinned down before spending RAM on a real editor launch.

Checklist:
  1. AutomationLibrary screenshot entry points
  2. EditorLevelLibrary viewport camera control
  3. SceneCapture2D as a headless-friendly alternative
  4. file-writing helpers so the result can be inspected afterwards
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art77'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A77: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def main():
    p('=== A. AutomationLibrary ===')
    has = hasattr(unreal, 'AutomationLibrary')
    p('  AutomationLibrary: %s' % has)
    if has:
        ms = [m for m in dir(unreal.AutomationLibrary) if not m.startswith('_')]
        p('  members: %s' % ms)
        for n in ms:
            if 'screenshot' in n.lower():
                p('    .%s -> %s' % (n, (getattr(unreal.AutomationLibrary, n).__doc__
                                          or '')[:400].replace('\r\n', ' ')))

    p('')
    p('=== B. EditorLevelLibrary camera control ===')
    ELL = [m for m in dir(unreal.EditorLevelLibrary) if not m.startswith('_')]
    for n in ELL:
        if any(k in n.lower() for k in ('viewport', 'camera', 'view')):
            p('  .%s -> %s' % (n, (getattr(unreal.EditorLevelLibrary, n).__doc__
                                    or '')[:300].replace('\r\n', ' ')))

    p('')
    p('=== C. capture actors ===')
    for n in ('SceneCapture2D', 'SceneCaptureComponent2D', 'TextureRenderTarget2D',
              'HighResScreenshot', 'ScreenshotRequest'):
        p('  unreal.%-28s %s' % (n, hasattr(unreal, n)))
    for n in ('SceneCapture2D', 'SceneCaptureComponent2D'):
        o = getattr(unreal, n, None)
        if o is not None:
            p('  %s capture source enum: %s' % (n, [
                a for a in dir(unreal.SceneCaptureSource) if not a.startswith('_')]
                if hasattr(unreal, 'SceneCaptureSource') else 'n/a'))

    p('')
    p('=== D. editor viewport / unrealEd availability in a commandlet ===')
    for n in ('EditorLevelLibrary', 'UnrealEdSubsystem', 'LevelEditorSubsystem',
              'EditorActorSubsystem', 'AssetEditorSubsystem',
              'EditorScriptingSubsystem', 'EditorLoadingAndSavingUtils'):
        p('  unreal.%-32s %s' % (n, hasattr(unreal, n)))
    for n in ('LevelEditorSubsystem', 'UnrealEdSubsystem'):
        o = getattr(unreal, n, None)
        if o is not None:
            p('  %s members: %s' % (n, sorted(
                m for m in dir(o) if not m.startswith('_'))[:60]))

    p('')
    p('=== E. can a commandlet even reach a viewport? ===')
    p('  GEditor: %s' % (hasattr(unreal, 'EditorUtilityLibrary')))
    v = unreal.EditorLevelLibrary.get_editor_world()
    p('  editor world: %s' % (v.get_name() if v else None))
    try:
        cm = unreal.get_editor_subsystem(unreal.UnrealEdSubsystem)
        p('  UnrealEdSubsystem instance: %s' % cm)
        if cm:
            p('    has play_in_viewport: %s' % hasattr(cm, 'play_in_viewport'))
    except Exception as exc:
        p('  UnrealEdSubsystem -> %r' % str(exc)[:150])

    p('')
    p('=== F. render target route (would work without a viewport) ===')
    if hasattr(unreal, 'TextureRenderTarget2D'):
        p('  TextureRenderTarget2D factory symbols: %s' % [
            n for n in dir(unreal) if 'RenderTargetFactory' in n][:10])

    p('')
    p('=== G. image write helpers ===')
    for n in ('ImageWriteQueue', 'ImageWriteFunctionLibrary', 'ImageUtils',
              'FImageUtils', 'ImagePixelData'):
        p('  unreal.%-28s %s' % (n, hasattr(unreal, n)))
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A77_FATAL')
