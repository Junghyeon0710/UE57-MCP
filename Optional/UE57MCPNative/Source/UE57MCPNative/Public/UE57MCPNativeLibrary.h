// Copyright 2026 Junghyeon0710. SPDX-License-Identifier: Apache-2.0

#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "UE57MCPNativeLibrary.generated.h"

/**
 * @brief Python에 노출되지 않은 5.7 그래프와 위젯 트리 편집을 제공한다.
 */
UCLASS()
class UE57MCPNATIVE_API UUE57MCPNativeLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** @brief 에디터 메인 스레드에서 JSON 명령을 실행하고 성공 여부와 결과를 반환한다. */
    UFUNCTION(BlueprintCallable, Category = "UE57 MCP")
    static FString Execute(const FString& Operation, const FString& ArgumentsJson);
};
