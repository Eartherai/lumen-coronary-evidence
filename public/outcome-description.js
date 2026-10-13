/** Recorded-label comparison at the exact currently displayed decision rule. */
export function describeOutcome(probability, threshold, truth){
  if(![probability,threshold].every(v=>Number.isFinite(v)&&v>=0&&v<=1)||![0,1].includes(truth))throw Error('Invalid outcome comparison');
  const flag=Number(probability>=threshold),match=flag===truth;
  return {flag,match,kind:match?'agreement':truth?'missed_positive':'false_alarm',
    text:match?'agrees':truth?'missed positive':'false alarm'};
}
