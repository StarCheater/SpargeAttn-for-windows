import os
import sys
import platform
import warnings
from pathlib import Path

from setuptools import setup, find_packages
from torch.utils.cpp_extension import BuildExtension, CUDAExtension, CUDA_HOME

# Определение платформы для условной компиляции
IS_WINDOWS = sys.platform == 'win32'

# Получение версии пакета из переменной окружения или файла
def get_version():
    version = '1.0.0'
    suffix = os.environ.get("SPARGEATTN_WHEEL_VERSION_SUFFIX", "")
    return version + suffix

# Проверка наличия CUDA
if CUDA_HOME is None:
    raise RuntimeError("CUDA_HOME environment variable is not set. Please install CUDA toolkit.")

# Условные флаги компилятора для C++ с подавлением D9025
if IS_WINDOWS:
    # Флаги MSVC для Windows с подавлением предупреждений
    CXX_FLAGS = [
        '/std:c++17',      # Стандарт C++17
        '/O2',             # Оптимизация уровня 2
        '/MD',             # Многопоточная DLL среда выполнения
        '/EHsc',           # Обработка исключений C++
        '/DNOMINMAX',      # Отключение макросов min/max
        '/W0',             # Подавление всех предупреждений (избегает D9025)
    ]
    LINK_FLAGS = []
else:
    # Флаги GCC/Clang для Linux/Mac
    CXX_FLAGS = [
        '-std=c++17',      # Стандарт C++17
        '-O3',             # Максимальная оптимизация
        '-fopenmp',        # Поддержка OpenMP
        '-w',              # Подавление всех предупреждений
    ]
    LINK_FLAGS = ['-lgomp']

# Базовые флаги NVCC с подавлением #177-D
NVCC_FLAGS = [
    '-std=c++17',                      # Стандарт C++17 для CUDA
    '-O3',                             # Максимальная оптимизация
    '-U__CUDA_NO_HALF_OPERATORS__',    # Разрешение half-операторов
    '-U__CUDA_NO_HALF_CONVERSIONS__',  # Разрешение half-конверсий
    '--use_fast_math',                 # Быстрые математические функции
    '--expt-relaxed-constexpr',        # Экспериментальная поддержка constexpr
    '--diag-suppress=177',             # Подавление предупреждения #177-D
    '-w',                              # Подавление всех NVCC предупреждений
]

# Определение compute capabilities из переменной окружения
arch_list = os.environ.get('TORCH_CUDA_ARCH_LIST', '8.0;8.6;8.9;9.0')
if arch_list:
    for arch in arch_list.split(';'):
        arch_clean = arch.replace('.', '')
        NVCC_FLAGS.extend([
            '-gencode', f'arch=compute_{arch_clean},code=sm_{arch_clean}'
        ])

# Добавление флагов для verbose вывода и отладки (с подавлением предупреждений)
if IS_WINDOWS:
    import multiprocessing
    num_threads = min(multiprocessing.cpu_count(), 8)
    NVCC_FLAGS.extend([
        f'--threads={num_threads}',    # Количество потоков компиляции
    ])
else:
    NVCC_FLAGS.extend([
        '--threads=8',
    ])

# Поиск исходных файлов проекта
sources = []
csrc_dir = Path(__file__).parent / 'csrc'

# Добавление C++ исходных файлов
cpp_files = list(csrc_dir.glob('*.cpp'))
sources.extend([str(f) for f in cpp_files])

# Добавление CUDA исходных файлов
cu_files = list(csrc_dir.glob('*.cu'))
sources.extend([str(f) for f in cu_files])

# Проверка наличия исходных файлов
if not sources:
    warnings.warn("No source files found in csrc directory")
    sources = ['csrc/dummy.cpp']  # Создание заглушки если файлы не найдены

# Создание CUDA расширения
ext_modules = [
    CUDAExtension(
        name='spas_sage_attn._C',      # Имя модуля расширения
        sources=sources,               # Список исходных файлов
        include_dirs=[                 # Директории заголовочных файлов
            str(csrc_dir),
            str(Path(__file__).parent / 'spas_sage_attn')
        ],
        extra_compile_args={           # Дополнительные флаги компиляции
            'cxx': CXX_FLAGS,          # Флаги для C++ компилятора
            'nvcc': NVCC_FLAGS         # Флаги для NVCC компилятора
        },
        extra_link_args=LINK_FLAGS,    # Флаги линковки
        define_macros=[                # Макросы препроцессора
            ('WITH_CUDA', None),       # Включение CUDA поддержки
            ('TORCH_EXTENSION_NAME', 'spas_sage_attn._C')
        ]
    )
]

# Чтение README файла для описания пакета
readme_path = Path(__file__).parent / 'README.md'
long_description = ''
if readme_path.exists():
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

# Настройка пакета
setup(
    name='spas_sage_attn',                         # Имя пакета
    version=get_version(),                         # Версия пакета
    description='Universal sparse attention for Windows',  # Краткое описание
    long_description=long_description,             # Полное описание из README
    long_description_content_type='text/markdown', # Тип разметки описания
    author='SpargeAttn team',                      # Автор
    author_email='',                               # Email автора
    url='https://github.com/StarCheater/SpargeAttn-for-windows',  # URL проекта
    license='Apache 2.0',                         # Лицензия
    packages=find_packages(),                      # Автоматический поиск пакетов
    python_requires='>=3.9',                      # Минимальная версия Python
    install_requires=[                             # Зависимости
        'torch>=2.3.0',                           # PyTorch с CUDA поддержкой
        'ninja',                                   # Система сборки Ninja
        'packaging',                               # Утилиты для работы с версиями
        'pybind11>=2.12.0',                       # Привязки C++ к Python
    ],
    ext_modules=ext_modules,                       # CUDA расширения
    cmdclass={                                     # Кастомные команды сборки
        'build_ext': BuildExtension                # Использование PyTorch BuildExtension
    },
    zip_safe=False,                                # Пакет не может быть запущен из ZIP
    classifiers=[                                  # Классификаторы PyPI
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    keywords='attention sparse cuda pytorch machine learning',  # Ключевые слова
)
