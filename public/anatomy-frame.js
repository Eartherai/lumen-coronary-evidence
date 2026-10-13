/** Draw on input as well as animation ticks; only a successful draw completes a frame. */
export function createAnatomyFrameRenderer({isContextLost,draw,onSuccess,onFailure}) {
  let drawing=false,failed=false;
  return function renderFrame() {
    if(drawing||failed||isContextLost())return false;
    drawing=true;
    try {
      draw();
      onSuccess();
      return true;
    } catch(error) {
      failed=true;
      onFailure(error);
      return false;
    } finally {
      drawing=false;
    }
  };
}
