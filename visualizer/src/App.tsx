import { Hud } from "./components/Hud";
import { BrainGraph } from "./graph/BrainGraph";
import { useEventStream } from "./stream/useEventStream";

export default function App() {
  useEventStream();
  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <BrainGraph />
      <Hud />
    </div>
  );
}
