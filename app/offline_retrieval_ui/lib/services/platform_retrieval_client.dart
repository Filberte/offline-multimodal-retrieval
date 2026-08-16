import 'retrieval_client.dart';
import 'platform_retrieval_client_stub.dart'
    if (dart.library.io) 'platform_retrieval_client_io.dart'
    as implementation;

/// 根据运行平台选择本地进程客户端或只读演示客户端。
RetrievalClient createPlatformRetrievalClient() =>
    implementation.createPlatformRetrievalClient();