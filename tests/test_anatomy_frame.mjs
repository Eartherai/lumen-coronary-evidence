import test from 'node:test';
import assert from 'node:assert/strict';
import { createAnatomyFrameRenderer } from '../public/anatomy-frame.js';

test('An explicit anatomy frame is drawn and acknowledged before its caller resumes', () => {
  const events = [];
  const renderFrame = createAnatomyFrameRenderer({
    isContextLost: () => false,
    draw: () => events.push('draw'),
    onSuccess: () => events.push('success'),
    onFailure: error => assert.fail(`Unexpected render failure: ${error}`),
  });

  assert.deepEqual(events, []);
  const completed = renderFrame();
  events.push('caller resumed');

  assert.equal(completed, true);
  assert.deepEqual(events, ['draw', 'success', 'caller resumed']);
});

test('A drawing exception is reported as failure and never acknowledged as a completed frame', () => {
  const drawError = new Error('WebGL drawing failed');
  const failures = [];
  let successCount = 0;
  const renderFrame = createAnatomyFrameRenderer({
    isContextLost: () => false,
    draw: () => { throw drawError; },
    onSuccess: () => { successCount += 1; },
    onFailure: error => failures.push(error),
  });

  assert.equal(renderFrame(), false);
  assert.equal(successCount, 0);
  assert.deepEqual(failures, [drawError]);
});

test('A failing completion callback cannot return a successful frame or continue drawing', () => {
  const completionError = new Error('Frame completion could not be recorded');
  const failures = [];
  let drawCount = 0;
  let completionCount = 0;
  const renderFrame = createAnatomyFrameRenderer({
    isContextLost: () => false,
    draw: () => { drawCount += 1; },
    onSuccess: () => {
      completionCount += 1;
      throw completionError;
    },
    onFailure: error => failures.push(error),
  });

  assert.equal(renderFrame(), false);
  assert.equal(renderFrame(), false);
  assert.equal(drawCount, 1);
  assert.equal(completionCount, 1);
  assert.deepEqual(failures, [completionError]);
});

test('Context loss skips completion while a recovered context performs a genuine new draw', () => {
  let lost = true;
  let drawCount = 0;
  let successCount = 0;
  const failures = [];
  const renderFrame = createAnatomyFrameRenderer({
    isContextLost: () => lost,
    draw: () => { drawCount += 1; },
    onSuccess: () => { successCount += 1; },
    onFailure: error => failures.push(error),
  });

  assert.equal(renderFrame(), false);
  assert.equal(drawCount, 0);
  assert.equal(successCount, 0);

  lost = false;
  assert.equal(renderFrame(), true);
  assert.equal(drawCount, 1);
  assert.equal(successCount, 1);

  lost = true;
  assert.equal(renderFrame(), false);
  assert.equal(drawCount, 1);
  assert.equal(successCount, 1);

  lost = false;
  assert.equal(renderFrame(), true);
  assert.equal(drawCount, 2);
  assert.equal(successCount, 2);
  assert.deepEqual(failures, []);
});

test('A render requested from inside drawing cannot recursively draw or acknowledge another frame', () => {
  let drawCount = 0;
  let successCount = 0;
  let nestedResult;
  let renderFrame;
  renderFrame = createAnatomyFrameRenderer({
    isContextLost: () => false,
    draw: () => {
      drawCount += 1;
      if (drawCount === 1) nestedResult = renderFrame();
    },
    onSuccess: () => { successCount += 1; },
    onFailure: error => assert.fail(`Unexpected render failure: ${error}`),
  });

  assert.equal(renderFrame(), true);
  assert.equal(nestedResult, false);
  assert.equal(drawCount, 1);
  assert.equal(successCount, 1);

  assert.equal(renderFrame(), true);
  assert.equal(drawCount, 2);
  assert.equal(successCount, 2);
});

test('A render requested during completion cannot duplicate the acknowledged frame', () => {
  let drawCount = 0;
  let successCount = 0;
  let nestedResult;
  let renderFrame;
  renderFrame = createAnatomyFrameRenderer({
    isContextLost: () => false,
    draw: () => { drawCount += 1; },
    onSuccess: () => {
      successCount += 1;
      if (successCount === 1) nestedResult = renderFrame();
    },
    onFailure: error => assert.fail(`Unexpected render failure: ${error}`),
  });

  assert.equal(renderFrame(), true);
  assert.equal(nestedResult, false);
  assert.equal(drawCount, 1);
  assert.equal(successCount, 1);
});

test('After a drawing failure, repeated requests and context recovery cannot repeat the failed draw', () => {
  let lost = false;
  let drawCount = 0;
  let successCount = 0;
  const failures = [];
  const drawError = new Error('Drawing cannot continue');
  const renderFrame = createAnatomyFrameRenderer({
    isContextLost: () => lost,
    draw: () => {
      drawCount += 1;
      throw drawError;
    },
    onSuccess: () => { successCount += 1; },
    onFailure: error => failures.push(error),
  });

  assert.equal(renderFrame(), false);
  assert.equal(renderFrame(), false);
  lost = true;
  assert.equal(renderFrame(), false);
  lost = false;
  assert.equal(renderFrame(), false);

  assert.equal(drawCount, 1);
  assert.equal(successCount, 0);
  assert.deepEqual(failures, [drawError]);
});
