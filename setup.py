import os
import sys
import warnings
from pathlib import Path

from setuptools import setup, find_packages
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

# Определение платформы
IS_WINDOWS = sys.platform == 'win32'

# Получение версии пакета
def get_version():
    base = '1.0.0'
    suffix = os.environ.get("SPARGEATTN_WHEEL_VERSION_SUFFIX", "")
    return base + suffix

# Проверка и подхват CUDA_HOME
cuda_home = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
if not cuda_home:
    warnings.warn("CUDA_HOME не задан — сборка будет без CUDA", stacklevel=2)

# Флаги для C++ компилятора
if IS_WINDOWS:
    CXX_FLAGS = ['/std:c++17', '/O2', '/MD', '/EHsc']  # MSVC: стандарт, оптимизация, DLL, исключения[1]
else:
    CXX_FLAGS = ['-std=c++17', '-O3']  # GCC/Clang: стандарт, оптимизация[2]

# Флаги NVCC: стандарт, оптимизация, fast math, подавление предупреждений[3]
NVCC_FLAGS = [
    '-std=c++17', '-O3', '--use_fast_math',
    '--expt-relaxed-constexpr', '--diag-suppress=177', '-w'
]
# Архитектуры CUDA из окружения
archs = os.environ.get('TORCH_CUDA_ARCH_LIST', '8.0;8.6;8.9;9.0').split(';')
for a in archs:
    num = a.replace('.', '')
    NVCC_FLAGS += ['-gencode', f'arch=compute_{num},code=sm_{num}']

# Сбор исходных файлов
csrc_dir = Path(__file__).parent / 'csrc'
sources = [str(p) for ext in ('*.cpp','*.cu') for p in csrc_dir.glob(ext)]
if not sources:
    warnings.warn("csrc пуст — добавлена заглушка", stacklevel=2)
    sources = ['csrc/dummy.cpp']

# Определение расширения
ext_modules = []
if cuda_home:
    ext_modules.append(
        CUDAExtension(
            name='spas_sage_attn._C',
            sources=sources,
            include_dirs=[str(csrc_dir), str(Path(__file__).parent / 'spas_sage_attn')],
            extra_compile_args={'cxx': CXX_FLAGS, 'nvcc': NVCC_FLAGS},
            define_macros=[('WITH_CUDA', None)]
        )
    )
else:
    warnings.warn("CUDAExtension не добавлен — только Python пакеты", stacklevel=2)

# Чтение README
readme = Path(__file__).parent / 'README.md'
long_desc = readme.read_text(encoding='utf-8') if readme.exists() else ''

# Настройка setup()
setup(
    name='spas_sage_attn',
    version=get_version(),
    description='Universal sparse attention for Windows',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    author='SpargeAttn team',
    url='https://github.com/StarCheater/SpargeAttn-for-windows',
    license='Apache-2.0',
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=[
        'torch>=2.4.0+cu124', 'ninja', 'packaging', 'pybind11>=2.12.0'
    ],
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExtension},
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.9',
        'Operating System :: Microsoft :: Windows',
        'License :: OSI Approved :: Apache Software License'
    ],
    keywords='attention sparse cuda pytorch machine learning'
)
