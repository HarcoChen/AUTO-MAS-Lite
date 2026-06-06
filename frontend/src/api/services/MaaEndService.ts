/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MaaEndAvailableTasksIn } from '../models/MaaEndAvailableTasksIn';
import type { MaaEndAvailableTasksOut } from '../models/MaaEndAvailableTasksOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MaaEndService {
    /**
     * 获取 MaaEnd 动态任务和选项定义
     * 获取 MaaEnd 动态任务和选项定义
     *
     * 前端调用此接口获取 MaaEnd 预设模式可配置任务，
     * 用于动态渲染任务开关和 optionValues。
     * @param requestBody
     * @returns MaaEndAvailableTasksOut Successful Response
     * @throws ApiError
     */
    public static getMaaendAvailableTasksApiScriptsMaaendTasksAvailablePost(
        requestBody: MaaEndAvailableTasksIn,
    ): CancelablePromise<MaaEndAvailableTasksOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/scripts/maaend/tasks/available',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
