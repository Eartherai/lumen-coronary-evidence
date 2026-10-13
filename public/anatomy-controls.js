/** View controls for the existing generic reference meshes; no model inference. */
export function installAnatomyControls({THREE, camera, controls, meshes, container, onViewChange=()=>{}}) {
  const document = container.ownerDocument;
  const arteries = ['LAD', 'LCX', 'RCA'];
  const overviewPosition = new THREE.Vector3(35, 22, 285);
  const group = document.createElement('div');
  group.className = 'anatomy-controls';
  group.setAttribute('role', 'group');
  group.setAttribute('aria-label', 'Reference anatomy views');

  function button(label, action) {
    const element = document.createElement('button');
    element.type = 'button';
    element.className = 'anatomy-control secondary compact';
    element.textContent = label;
    if (container.id) element.setAttribute('aria-controls', container.id);
    element.addEventListener('click', action);
    group.append(element);
    return element;
  }

  const overview = button('Overview', () => {
    isolate.checked = false;
    applyIsolation();
    showOverview();
    status.textContent = 'Overview of all reference vessels.';
  });
  overview.title = 'Restore the full reference-heart overview';

  const opposite = button('Opposite view', () => {
    const direction = camera.position.clone().sub(controls.target);
    if (direction.lengthSq() < 1e-12) direction.copy(overviewPosition);
    const up = camera.up.clone();
    if (up.lengthSq() < 1e-12) up.set(0, 1, 0);
    direction.applyAxisAngle(up.normalize(), Math.PI);
    camera.position.copy(controls.target).add(direction);
    controls.update();
    status.textContent = 'Opposite viewpoint of the same reference anatomy.';
  });
  opposite.title = 'Turn the viewpoint halfway around its current target';

  const focus = button('Focus artery', () => {
    if (!validArtery()) return;
    const mesh = meshes[selected];
    mesh.updateWorldMatrix(true, true);
    const bounds = new THREE.Box3().setFromObject(mesh);
    if (bounds.isEmpty()) {
      status.textContent = 'The selected reference artery has no displayable bounds.';
      return;
    }
    const sphere = bounds.getBoundingSphere(new THREE.Sphere());
    const direction = camera.position.clone().sub(controls.target);
    if (direction.lengthSq() < 1e-12) direction.copy(overviewPosition);
    direction.normalize();
    const verticalHalfAngle = THREE.MathUtils.degToRad(camera.fov / 2);
    const horizontalHalfAngle = Math.atan(Math.tan(verticalHalfAngle) * Math.max(camera.aspect, 0.01));
    const halfAngle = Math.max(0.01, Math.min(verticalHalfAngle, horizontalHalfAngle));
    const desiredDistance = Math.max(sphere.radius, 1) / Math.sin(halfAngle) * 1.2;
    const minimum = Number.isFinite(controls.minDistance) ? controls.minDistance : 0;
    const maximum = Number.isFinite(controls.maxDistance) ? controls.maxDistance : Infinity;
    const distance = Math.min(maximum, Math.max(minimum, desiredDistance));
    controls.target.copy(sphere.center);
    camera.position.copy(sphere.center).addScaledVector(direction, distance);
    controls.update();
    status.textContent = `${selected} reference vessel centered in the view.`;
  });
  focus.title = 'Center and fit the selected reference artery using its mesh bounds';

  const isolateLabel = document.createElement('label');
  isolateLabel.className = 'anatomy-isolate';
  const isolate = document.createElement('input');
  isolate.type = 'checkbox';
  if (container.id) isolate.setAttribute('aria-controls', container.id);
  isolate.addEventListener('change', () => {
    applyIsolation();
    status.textContent = isolate.checked ? `Only the ${selected} reference vessel is visible.` : 'All reference vessels restored.';
  });
  isolateLabel.append(isolate, document.createTextNode('Isolate artery'));
  group.append(isolateLabel);

  const status = document.createElement('span');
  status.className = 'anatomy-control-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.setAttribute('aria-atomic', 'true');
  group.append(status);
  const panel = container.closest('.anatomy-panel');
  const toolbar = panel?.querySelector('.anatomy-tools') || panel?.querySelector('.viewer-toolbar');
  (toolbar || container).append(group);

  let selected = null;
  let wasIsolated = false;
  let visibilityBeforeIsolation = new Map();

  function validArtery() {
    return arteries.includes(selected) && Boolean(meshes[selected]);
  }

  function showOverview() {
    controls.target.set(0, 0, 0);
    camera.position.copy(overviewPosition);
    controls.update();
  }

  function applyIsolation() {
    const enabled = isolate.checked && validArtery();
    if (enabled) {
      if (!wasIsolated) visibilityBeforeIsolation = new Map(Object.entries(meshes).map(([key, mesh]) => [key, mesh.visible]));
      for (const [key, mesh] of Object.entries(meshes)) mesh.visible = key === selected;
      wasIsolated = true;
      syncLabels();
      return;
    }
    if (wasIsolated) {
      for (const [key, mesh] of Object.entries(meshes)) mesh.visible = visibilityBeforeIsolation.get(key) ?? true;
      wasIsolated = false;
    }
    // Respect the user's current surface checkbox even if it changed during isolation.
    const surface = container.querySelector('#shell-toggle');
    if (surface && meshes.heart) meshes.heart.visible = surface.checked;
    syncLabels();
  }

  function syncLabels() {
    for (const tag of container.querySelectorAll('.vessel-tag')) {
      const key = tag.textContent.trim();
      if (meshes[key]) tag.style.display = meshes[key].visible ? '' : 'none';
    }
    onViewChange();
  }

  function update(nextSelected) {
    const previousSelected = selected;
    selected = nextSelected;
    const valid = validArtery();
    focus.disabled = !valid;
    isolate.disabled = !valid;
    if (!valid) isolate.checked = false;
    applyIsolation();
    if (selected === 'CAD' && previousSelected !== 'CAD') showOverview();
    status.textContent = valid
      ? (isolate.checked ? `Only the ${selected} reference vessel is visible.` : `${selected} reference vessel selected.`)
      : 'Select LAD, LCX or RCA to focus or isolate an artery.';
  }

  update(null);
  return {update};
}
