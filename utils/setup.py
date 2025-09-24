import sys
import glob
import os
from setuptools import setup, Extension
from Cython.Build import cythonize

# Thư mục hiện tại (nơi chứa setup.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Thư mục output build an toàn
output_dir = os.path.abspath(os.path.join(script_dir, "..", "utils_ext"))
os.makedirs(output_dir, exist_ok=True)

# Danh sách các file cần build
source_files = ["db.py", "generate_ipv6.py", "proxy.py", "slm_save_data.py"]

# Khởi tạo danh sách extensions
extensions = []
for file_name in source_files:
    source_path = os.path.join(script_dir, file_name)

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"❌ Không tìm thấy file: {file_name}")

    ext_name = os.path.splitext(file_name)[0]

    extensions.append(
        Extension(
            name=ext_name,
            sources=[source_path],
            language="c",
            define_macros=[("NDEBUG", None)],
            extra_compile_args=(
                ["/O2", "/Wall", "/DNDEBUG"]
                if sys.platform == "win32"
                else ["-O2", "-Wall", "-DNDEBUG"]
            ),
            extra_link_args=[],
        )
    )

# Thực thi build
setup(
    name="im_utils",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "always_allow_keywords": False,
            "embedsignature": False,
            "binding": False,
            "infer_types": True,
            "nonecheck": False,
            "cdivision": True,
            "wraparound": False,
        },
    ),
    options={"build_ext": {"build_lib": output_dir}},
    script_args=["build_ext"],
)

# 🧹 Xoá file .c, .pyd, .so sau build (trừ thư mục output)
cleanup_exts = [".c", ".pyd", ".so"]
for ext in cleanup_exts:
    for file in glob.glob(os.path.join(script_dir, f"*{ext}")):
        try:
            os.remove(file)
            print(f"🗑️ Đã xóa: {file}")
        except Exception as e:
            print(f"⚠️ Lỗi khi xóa {file}: {e}")

print(f"✅ Build thành công! File đã nằm trong: {output_dir}")
