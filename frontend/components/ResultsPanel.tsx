export default function ResultsPanel({ result }: any) {
  return (
    <div>
      <p>Past Cover (ha): {result.past_cover_ha}</p>
      <p>Present Cover (ha): {result.present_cover_ha}</p>
      <p>Change (ha): {result.change_ha}</p>
      <p>Change (%): {result.percent_change}</p>
    </div>
  );
}
