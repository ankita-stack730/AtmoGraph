"""
AtmoGraph GraphSAGE model.

Small CPU-friendly GraphSAGE network for node-level
supply-chain ripple-risk prediction.
"""

import torch
from torch import nn
from torch_geometric.nn import SAGEConv


class AtmoGraphGraphSAGE(nn.Module):
    """
    GraphSAGE model for node-level risk prediction.

    Input:
        Node feature vectors.

    Output:
        One risk logit per node.
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 32,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        if num_layers < 2:
            raise ValueError("num_layers must be at least 2")

        self.convs = nn.ModuleList()

        # First GraphSAGE layer
        self.convs.append(
            SAGEConv(in_channels, hidden_channels)
        )

        # Additional GraphSAGE layers
        for _ in range(num_layers - 2):
            self.convs.append(
                SAGEConv(hidden_channels, hidden_channels)
            )

        # Final GraphSAGE layer
        self.convs.append(
            SAGEConv(hidden_channels, hidden_channels)
        )

        self.dropout = nn.Dropout(dropout)

        # Node-level risk prediction head
        self.risk_head = nn.Linear(hidden_channels, 1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        """
        Run GraphSAGE message passing and return node risk logits.

        Returns:
            Tensor of shape [num_nodes].
        """

        for conv in self.convs:
            x = conv(x, edge_index)
            x = torch.relu(x)
            x = self.dropout(x)

        logits = self.risk_head(x).squeeze(-1)

        return logits

    def predict_risk(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        """
        Return node risk probabilities in the range [0, 1].
        """

        logits = self.forward(x, edge_index)

        return torch.sigmoid(logits)