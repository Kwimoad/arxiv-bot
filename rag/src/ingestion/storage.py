import pyarrow as pa
import pyarrow.parquet as pq

from ...config import OUTPUT_DIR

def save_metadata_batch(
        metadata_list : list[dict],
        batch_number : int
):
    
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        OUTPUT_DIR / f"batch_{batch_number:05d}.parquet"
    )

    table = pa.Table.from_pylist(
        metadata_list
    )

    pq.write_table(
        table,
        output_file,
        compression = "zstd"
    )

    return output_file