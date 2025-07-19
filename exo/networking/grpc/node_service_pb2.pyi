from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Shard(_message.Message):
    __slots__ = ("model_id", "start_layer", "end_layer", "n_layers")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    START_LAYER_FIELD_NUMBER: _ClassVar[int]
    END_LAYER_FIELD_NUMBER: _ClassVar[int]
    N_LAYERS_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    start_layer: int
    end_layer: int
    n_layers: int
    def __init__(self, model_id: _Optional[str] = ..., start_layer: _Optional[int] = ..., end_layer: _Optional[int] = ..., n_layers: _Optional[int] = ...) -> None: ...

class PromptRequest(_message.Message):
    __slots__ = ("shard", "prompt", "request_id", "inference_state")
    SHARD_FIELD_NUMBER: _ClassVar[int]
    PROMPT_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    INFERENCE_STATE_FIELD_NUMBER: _ClassVar[int]
    shard: Shard
    prompt: str
    request_id: str
    inference_state: InferenceState
    def __init__(self, shard: _Optional[_Union[Shard, _Mapping]] = ..., prompt: _Optional[str] = ..., request_id: _Optional[str] = ..., inference_state: _Optional[_Union[InferenceState, _Mapping]] = ...) -> None: ...

class TensorRequest(_message.Message):
    __slots__ = ("shard", "tensor", "request_id", "inference_state")
    SHARD_FIELD_NUMBER: _ClassVar[int]
    TENSOR_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    INFERENCE_STATE_FIELD_NUMBER: _ClassVar[int]
    shard: Shard
    tensor: Tensor
    request_id: str
    inference_state: InferenceState
    def __init__(self, shard: _Optional[_Union[Shard, _Mapping]] = ..., tensor: _Optional[_Union[Tensor, _Mapping]] = ..., request_id: _Optional[str] = ..., inference_state: _Optional[_Union[InferenceState, _Mapping]] = ...) -> None: ...

class ExampleRequest(_message.Message):
    __slots__ = ("shard", "example", "target", "length", "train", "request_id")
    SHARD_FIELD_NUMBER: _ClassVar[int]
    EXAMPLE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    TRAIN_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    shard: Shard
    example: Tensor
    target: Tensor
    length: Tensor
    train: bool
    request_id: str
    def __init__(self, shard: _Optional[_Union[Shard, _Mapping]] = ..., example: _Optional[_Union[Tensor, _Mapping]] = ..., target: _Optional[_Union[Tensor, _Mapping]] = ..., length: _Optional[_Union[Tensor, _Mapping]] = ..., train: bool = ..., request_id: _Optional[str] = ...) -> None: ...

class Loss(_message.Message):
    __slots__ = ("loss", "grads")
    LOSS_FIELD_NUMBER: _ClassVar[int]
    GRADS_FIELD_NUMBER: _ClassVar[int]
    loss: float
    grads: Tensor
    def __init__(self, loss: _Optional[float] = ..., grads: _Optional[_Union[Tensor, _Mapping]] = ...) -> None: ...

class Tensor(_message.Message):
    __slots__ = ("tensor_data", "shape", "dtype")
    TENSOR_DATA_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    DTYPE_FIELD_NUMBER: _ClassVar[int]
    tensor_data: bytes
    shape: _containers.RepeatedScalarFieldContainer[int]
    dtype: str
    def __init__(self, tensor_data: _Optional[bytes] = ..., shape: _Optional[_Iterable[int]] = ..., dtype: _Optional[str] = ...) -> None: ...

class TensorList(_message.Message):
    __slots__ = ("tensors",)
    TENSORS_FIELD_NUMBER: _ClassVar[int]
    tensors: _containers.RepeatedCompositeFieldContainer[Tensor]
    def __init__(self, tensors: _Optional[_Iterable[_Union[Tensor, _Mapping]]] = ...) -> None: ...

class InferenceState(_message.Message):
    __slots__ = ("tensor_data", "tensor_list_data", "other_data_json")
    class TensorDataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Tensor
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Tensor, _Mapping]] = ...) -> None: ...
    class TensorListDataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: TensorList
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[TensorList, _Mapping]] = ...) -> None: ...
    TENSOR_DATA_FIELD_NUMBER: _ClassVar[int]
    TENSOR_LIST_DATA_FIELD_NUMBER: _ClassVar[int]
    OTHER_DATA_JSON_FIELD_NUMBER: _ClassVar[int]
    tensor_data: _containers.MessageMap[str, Tensor]
    tensor_list_data: _containers.MessageMap[str, TensorList]
    other_data_json: str
    def __init__(self, tensor_data: _Optional[_Mapping[str, Tensor]] = ..., tensor_list_data: _Optional[_Mapping[str, TensorList]] = ..., other_data_json: _Optional[str] = ...) -> None: ...

class CollectTopologyRequest(_message.Message):
    __slots__ = ("visited", "max_depth")
    VISITED_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    visited: _containers.RepeatedScalarFieldContainer[str]
    max_depth: int
    def __init__(self, visited: _Optional[_Iterable[str]] = ..., max_depth: _Optional[int] = ...) -> None: ...

class Topology(_message.Message):
    __slots__ = ("nodes", "peer_graph")
    class NodesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: DeviceCapabilities
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[DeviceCapabilities, _Mapping]] = ...) -> None: ...
    class PeerGraphEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: PeerConnections
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[PeerConnections, _Mapping]] = ...) -> None: ...
    NODES_FIELD_NUMBER: _ClassVar[int]
    PEER_GRAPH_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.MessageMap[str, DeviceCapabilities]
    peer_graph: _containers.MessageMap[str, PeerConnections]
    def __init__(self, nodes: _Optional[_Mapping[str, DeviceCapabilities]] = ..., peer_graph: _Optional[_Mapping[str, PeerConnections]] = ...) -> None: ...

class PeerConnection(_message.Message):
    __slots__ = ("to_id", "description")
    TO_ID_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    to_id: str
    description: str
    def __init__(self, to_id: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class PeerConnections(_message.Message):
    __slots__ = ("connections",)
    CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    connections: _containers.RepeatedCompositeFieldContainer[PeerConnection]
    def __init__(self, connections: _Optional[_Iterable[_Union[PeerConnection, _Mapping]]] = ...) -> None: ...

class DeviceFlops(_message.Message):
    __slots__ = ("fp32", "fp16", "int8")
    FP32_FIELD_NUMBER: _ClassVar[int]
    FP16_FIELD_NUMBER: _ClassVar[int]
    INT8_FIELD_NUMBER: _ClassVar[int]
    fp32: float
    fp16: float
    int8: float
    def __init__(self, fp32: _Optional[float] = ..., fp16: _Optional[float] = ..., int8: _Optional[float] = ...) -> None: ...

class DeviceCapabilities(_message.Message):
    __slots__ = ("model", "chip", "memory", "flops")
    MODEL_FIELD_NUMBER: _ClassVar[int]
    CHIP_FIELD_NUMBER: _ClassVar[int]
    MEMORY_FIELD_NUMBER: _ClassVar[int]
    FLOPS_FIELD_NUMBER: _ClassVar[int]
    model: str
    chip: str
    memory: int
    flops: DeviceFlops
    def __init__(self, model: _Optional[str] = ..., chip: _Optional[str] = ..., memory: _Optional[int] = ..., flops: _Optional[_Union[DeviceFlops, _Mapping]] = ...) -> None: ...

class SendResultRequest(_message.Message):
    __slots__ = ("request_id", "result", "tensor", "is_finished")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    TENSOR_FIELD_NUMBER: _ClassVar[int]
    IS_FINISHED_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    result: _containers.RepeatedScalarFieldContainer[int]
    tensor: Tensor
    is_finished: bool
    def __init__(self, request_id: _Optional[str] = ..., result: _Optional[_Iterable[int]] = ..., tensor: _Optional[_Union[Tensor, _Mapping]] = ..., is_finished: bool = ...) -> None: ...

class SendOpaqueStatusRequest(_message.Message):
    __slots__ = ("request_id", "status")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    status: str
    def __init__(self, request_id: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("is_healthy",)
    IS_HEALTHY_FIELD_NUMBER: _ClassVar[int]
    is_healthy: bool
    def __init__(self, is_healthy: bool = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
