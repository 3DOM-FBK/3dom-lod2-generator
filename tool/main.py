import os
import argparse



def parse_args():
    parser = argparse.ArgumentParser(description="Process 3D buildings from shapefile in Blender.")

    parser.add_argument("-i", "--input_shapefile", type=str, required=True,
                        help="Path to the input shapefile.")

    parser.add_argument("-o", "--output_folder", type=str, required=True,
                        help="Folder where the generated meshes will be saved.")

    parser.add_argument("-r", "--round_edges", action="store_true",
                        help="Apply rounding (bevel) to roof edges.")

    # parser.add_argument("--roof_attr", type=str, default="roof_type",
    #                     help="Attribute name in shapefile defining roof type (default: roof_type).")

    # parser.add_argument("--height_attr", type=str, default="height",
    #                     help="Attribute name in shapefile defining building height (default: height).")

    parser.add_argument("--export_format", type=str, default="ply", choices=["ply", "obj"],
                        help="File format to export the resulting mesh (default: ply).")
    
    parser.add_argument("--las", type=str,
                        help="Las file")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    cmd = f"blender -b --python /app/tool/blender_main.py > /dev/null 2>&1 -- -i {args.input_shapefile} -o {args.output_folder} --export_format {args.export_format} --las {args.las}"
    # cmd = f"blender -b --python /app/tool/blender_main.py -- -i {args.input_shapefile} -o {args.output_folder} --export_format {args.export_format} --las {args.las}"

    if args.round_edges:
        cmd += " -r"
    
    os.system(cmd)

