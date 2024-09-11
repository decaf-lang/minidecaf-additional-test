# minidecaf-tests

MiniDecaf 大实验测例及测试脚本。

本仓库fork自[minidecaf-test](https://github.com/decaf-lang/minidecaf-tests)

仓库中testcases文件夹下的step 1-12为基础实验测试样例，additional为附加测试，performance为性能测试仓库。

performance测试样例仓库下，你会看到一个`xxx.c`文件和一个`xxx.in`文件，其中`xxx.in`为本测试样例的输入。

## 使用说明

预置条件：qemu-user, riscv64-unknown-elf工具链，python3

```sh
python test.py -t <testcase_folder> [-p] [-b]
```

其中`-t`选项指定了存放测例的路径。`-b`和`-p`是可选项，使用`-b`将启用性能评测记录程序运行时间, 设置`-p`将开启并行评测（不建议在最终评测性能时启用）。

请看`test.py`，修改`compiler_path`,`compiler_args`和`gcc_args`变量，改为你的编译器路径和参数选项。

例如
```Python
compiler_path = "./build/mycompiler"
compiler_args = "-O2"
```
此处`compiler_args`为提供给你的编译器的额外选项。

我们会以下面的命令模板调用你的编译器生成汇编代码
```bash
# {compiler_path} {compiler_args} xxx.sy -o xxx.s
./build/mycompiler -O2 xxx.sy -o xxx.s
```
如果你的编译器不支持这样的命令格式，请在`test`函数中的注释附近修改。

然后会带上`gcc_args`使用gcc来汇编上一步生成的代码并链接运行时库。

比如：
```Python
gcc_args = "-march=rv64gc -mabi=lp64f"
```

则会调用
```bash
# riscv64-unknown-elf-gcc {gcc_args} xxx.s runtime/libsysy.a -o xxx
riscv64-unknown-elf-gcc -march=rv64gc -mabi=lp64f xxx.s runtime/libsysy.a -o xxx
```

## 如果你的编译器后端架构不是riscv64

重新编译libsysy.a，到runtime目录下，修改Makefile

修改CC变量，将`-march=rv64gc -mabi=lp64f`改为你的架构

重新`make`

推荐32位的用`-march=rv32gc -mabi=ilp32f`

64位的用：`-march=rv64gc -mabi=lp64f`


测试脚本还在不断完善中...