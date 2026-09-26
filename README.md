# 车队调度与维护管理平台

## Docker 快速启动

```bash
cp .env.example .env
docker compose up -d
```

前端：http://localhost:18708  
后端：http://localhost:19208/api/health/

## 项目介绍

面向物流公司和车队管理者的全栈 Web 应用，覆盖车辆档案、司机管理、调度派单、油耗统计和维保记录。

## 主要功能

- 调度中心：创建调度单、指派车辆和司机、查看运输时间线；**建单与发车自动执行司机班次合规预检**。
- 车辆管理：车辆卡片、维保历史、油耗趋势入口。
- 司机管理：状态筛选、调度历史、驾驶时长统计；**档案可配置每日驾驶上限、任务间最短休息、夜间连续休息（22:00-次日06:00）**。
- 维保管理：维修日历、费用统计、到期高亮。
- 油耗分析：油耗趋势、月度总油耗、异常油耗预警。

## 司机班次合规预检

- 司机档案三项配置（均为分钟，0 表示不限制）：`dailyDriveLimitMinutes` 每日驾驶上限、
  `minRestMinutes` 相邻任务最短休息、`nightRestMinutes` 夜间最短连续休息。
- 建单（`POST /api/dispatch-orders/`）与发车（`POST /api/dispatch-orders/{id}/start/`）时，
  按已有计划（Assigned/InProgress）与完成记录（Completed）核对：
  当日累计驾驶（按日历日切分）、与相邻任务的间隔、跨夜空档中的夜间连续休息、任务时间重叠。
- 冲突时返回 HTTP 409，消息包含涉及单号与「还缺多少时间」，调度单不落库 / 不进入执行。
- 选人预检：`POST /api/dispatch-orders/precheck/`，返回 `{ eligible, reasons, violations, blockedUntil }`。
- 司机列表 `GET /api/drivers/?withSchedule=1` 携带今日累计、下次可接单时间、未来占用；
  `PATCH /api/drivers/{id}/` 更新合规配置。
- 后端首次启动会在空库写入演示数据（赵强昨夜长途、孙晨明日已排班），便于直接验证冲突场景。
- 后端规则测试：`cd backend && DB_ENGINE=django.db.backends.sqlite3 DB_NAME=/tmp/t.db python manage.py test fleet_app.tests_pkg`。

## 本地开发

后端默认监听 3000，前端开发服务器会把 `/api` 请求代理到后端。后端本地启动需要可连接的 PostgreSQL；如果没有本机 PostgreSQL，请优先使用 Docker Compose 启动完整环境。

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:3000
```

```bash
cd frontend
npm install
npm run dev
```

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | React 18 + TypeScript + Vite |
| UI | Ant Design 5 |
| 图表 | ECharts |
| 状态 | Zustand |
| 后端 | Django + Django REST Framework |
| 数据库 | PostgreSQL 15 |
| 认证 | SimpleJWT |

## 目录结构

```
frontend/src/
├── api/ stores/ types/ components/common/ hooks/ pages/ router/ utils/ constants/
backend/
├── fleet_app/views/ serializers/ services/ middleware/ models.py urls.py permissions.py admin.py
└── config/settings.py urls.py
```

## 环境变量

| 变量 | 说明 |
| --- | --- |
| COMPOSE_PROJECT_NAME | Docker Compose 项目名 |
| DB_NAME / DB_USER / DB_PASSWORD / DB_ROOT_PASSWORD | PostgreSQL 配置 |
| JWT_SECRET | JWT 密钥 |
| FRONTEND_PORT / BACKEND_PORT | 宿主机端口 |

## 枚举位置

- VehicleStatus：frontend/src/types/enums.ts；frontend/src/types/vehicle.ts；frontend/src/components/common/VehicleCard.tsx；backend/fleet_app/models.py；backend/fleet_app/services/vehicle_service.py
- DispatchStatus：frontend/src/types/enums.ts；frontend/src/types/dispatch.ts；frontend/src/hooks/useDispatch.ts；backend/fleet_app/models.py；backend/fleet_app/services/dispatch_service.py
- MaintenanceType：frontend/src/types/enums.ts；frontend/src/types/maintenance.ts；frontend/src/pages/MaintenanceManage.tsx；backend/fleet_app/models.py；backend/fleet_app/services/maintenance_service.py
- DriverStatus：frontend/src/types/enums.ts；frontend/src/types/driver.ts；backend/fleet_app/models.py；backend/fleet_app/services/driver_service.py

## License

MIT
