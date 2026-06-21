# 计划表(Plan)规范

## 1. 边界

计划表框架只处理日期，不理解专项业务。
计划表框架返回完整 key，不按字段拆解，也不根据 key 内容作业务判断。Key 可以是字符串，也可以是多层嵌套对象。MaaEnd 当前使用嵌套对象。

## 2. 通用计划表结构

MaaEnd 计划表的后端类型是 `MaaEndPlanConfig`。一张计划表包含基础信息和八个日期槽位：

```json
{
  "Info": {
    "Name": "材料周计划",
    "Mode": "Weekly"
  },
  "ALL": {
    "Key": {}
  },
  "Monday": {
    "Key": {}
  },
  "Tuesday": {
    "Key": {}
  },
  "Wednesday": {
    "Key": {}
  },
  "Thursday": {
    "Key": {}
  },
  "Friday": {
    "Key": {}
  },
  "Saturday": {
    "Key": {}
  },
  "Sunday": {
    "Key": {}
  }
}
```

各日期槽位只有一个框架字段：`Key`。框架把它当作不透明数据保存和返回。

`Info` 字段如下：

| 字段 | 可选值 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `Name` | 字符串 | `新 MaaEnd 计划表` | 计划表名称 |
| `Mode` | `ALL`、`Weekly` | `ALL` | 全局模式或周计划模式 |

## 3. 例子：MaaEnd key

MaaEnd 定义两种 key：协议空间和基质刷取。一个日期槽位只能选择其中一种。

### 3.1 协议空间

```json
{
  "ProtocolSpace": {
    "Tab": "OperatorProgression",
    "Task": "OperatorEXP",
    "RewardsSetOption": "RewardsSetB"
  }
}
```

字段含义：

| 字段 | 说明 |
| --- | --- |
| `Tab` | 协议空间页签 |
| `Task` | 该页签下的任务 |
| `RewardsSetOption` | 奖励组 |

`Tab` 和 `Task` 必须匹配：

| `Tab` | 显示名称 | 可用 `Task` |
| --- | --- | --- |
| `OperatorProgression` | 干员养成 | `OperatorEXP`、`Promotions`、`T-Creds`、`SkillUp` |
| `WeaponProgression` | 武器养成 | `WeaponEXP`、`WeaponTune` |
| `CrisisDrills` | 危境预演 | `AdvancedProgression1` 至 `AdvancedProgression5` |

任务显示名称：

| 配置值 | 显示名称 |
| --- | --- |
| `OperatorEXP` | 干员经验 |
| `Promotions` | 干员进阶 |
| `T-Creds` | 钱币收集 |
| `SkillUp` | 技能提升 |
| `WeaponEXP` | 武器经验 |
| `WeaponTune` | 武器进阶 |
| `AdvancedProgression1` | 高阶培养 I - D96钢样品四 |
| `AdvancedProgression2` | 高阶培养 II - 超距辉映管 |
| `AdvancedProgression3` | 高阶培养 III - 快子遴捡晶格 |
| `AdvancedProgression4` | 高阶培养 IV - 象限拟合液 |
| `AdvancedProgression5` | 高阶培养 V - 三相纳米片 |

`RewardsSetOption` 可以是 `RewardsSetA` 或 `RewardsSetB`。只有下列任务支持 A/B 奖励组：

- `OperatorEXP`
- `Promotions`
- `SkillUp`
- `WeaponTune`

其他任务固定使用 `RewardsSetA`。前端保存时会主动归一化，后端从固定配置生成 key 时也会执行相同规则。

### 3.2 基质刷取

```json
{
  "AutoEssence": {
    "Location": "VFTheHub"
  }
}
```

可用地点：

| 配置值 | 显示名称 |
| --- | --- |
| `VFTheHub` | 枢纽区 |
| `VFOriginiumSciencePark` | 源石研究园 |
| `VFOriginLodespring` | 矿脉源区 |
| `VFPowerPlateau` | 供能高地 |
| `WLWulingCity` | 武陵城区 |
| `WLQingboStockade` | 清波寨 |

## 4. 用户引用和固定模式

用户通过 `Info.PlanMode` 选择理智任务来源。

计划表引用有两类错误：

- UUID 无效、计划表被删除或找不到：`引用的理智任务计划表不存在`
- UUID 指向其他专项的计划表：`引用的计划表 <UUID> 类型不是 MaaEnd 计划表`

Key 结构错误时，MaaEnd 的 schema 校验会拒绝执行。例如 `Tab` 为 `OperatorProgression` 时，`Task` 不能填写 `WeaponEXP`。

## 5. 专项运行时处理（maaend为例）

### 7.1 ProtocolSpace key

MaaEnd 收到 `ProtocolSpace` key 后：

1. 找到第一项 `taskName == "ProtocolSpace"` 的任务并启用。
2. 将 `ProtocolSpaceTab.caseName` 设为 `Tab`。
3. 将名称等于 `Tab` 的选项设为 `Task`。
4. 将 `RewardsSetOption.caseName` 设为奖励组。
5. 同名的其他 `ProtocolSpace` 任务保持禁用。

如果 MaaEnd 配置中没有 `ProtocolSpace`，记录警告并跳过注入：

```text
当前 MaaEnd 配置中缺少 ProtocolSpace 任务，已跳过协议空间注入
```

### 7.2 AutoEssence key

MaaEnd 收到 `AutoEssence` key 后：

1. 找到第一项 `taskName == "AutoEssence"` 的任务并启用。
2. 将 `AutoEssenceSpecifiedLocation.caseName` 设为 `Location`。
3. 同名的其他 `AutoEssence` 任务保持禁用。

如果 MaaEnd 配置中没有 `AutoEssence`，记录警告并跳过注入：

```text
当前 MaaEnd 配置中缺少 AutoEssence 任务，已跳过基质刷取注入
```

## 6. 维护位置

| 范围 | 位置 | 作用 |
| --- | --- | --- |
| 通用日期-key 容器 | `app/models/config.py` 中的 `WeeklyKeyPlanConfig` | 保存槽位并按日期返回 key |
| MaaEnd API 契约 | `app/models/schema.py` | 定义两种嵌套 key 及枚举约束 |
| MaaEnd key 转换 | `app/models/config.py` | 固定配置转换、、运行前校验 |
| MaaEnd 任务注入 | `app/task/maaend/AutoProxy.py` | 解释 key 并修改 MaaEnd 任务 |
| 前端 key 工具 | `frontend/src/utils/maaEndProtocolSpace.ts` | 编辑、显示、归一化和兼容旧结构 |
| 计划表界面 | `frontend/src/views/plan/tables/MaaEndPlanTable.vue` | 编辑日期对应的 MaaEnd key |

专项必须拥有自己的 key schema、编辑界面和消费逻辑。不要把专项字段塞回计划表框架，也不要让框架根据 key 内容分派业务。
