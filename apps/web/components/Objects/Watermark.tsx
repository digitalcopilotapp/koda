// Funeral Academy is a self-hosted, self-branded deployment — the upstream
// "Made with LearnHouse" badge is never rendered. The component is kept as a
// no-op (instead of deleted) so the call sites stay identical to upstream and
// future merges don't conflict.
function Watermark() {
    return null
}

export default Watermark