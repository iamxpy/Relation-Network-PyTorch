import torch
import torch.nn as nn

class MLP(nn.Module):

    def __init__(self, input_dim, hidden_dims, output_dim, nonlinear=False, dropout=False):
        '''
        :param nonlinear: if False last layer is linear, if True is nonlinear. Default False.
        '''

        super(MLP, self).__init__()
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim
        self.nonlinear = nonlinear
        self.droput = dropout

        self.linears = nn.ModuleList([nn.Linear(self.input_dim, self.hidden_dims[0])])
        if self.droput:
            self.dropouts = nn.ModuleList([nn.Dropout(p=0.5) for i in range(len(hidden_dims))])

        for i in range(1,len(self.hidden_dims)):
            self.linears.append(nn.Linear(self.hidden_dims[i-1], self.hidden_dims[i]))
        self.linears.append(nn.Linear(self.hidden_dims[-1], self.output_dim))



        self.activation = torch.tanh

    def forward(self, x):
        '''
        :param x: (n_features)
        '''

        x = self.linears[0](x)
        x = self.activation(x)

        for i in range(1,len(self.hidden_dims)):
            x = self.linears[i](x)
            x = self.activation(x)
            if self.droput:
                x = self.dropouts[i-1](x)

        out = self.linears[-1](x)
        if self.nonlinear:
            out = self.activation(out)
        if self.droput:
            out = self.dropouts[-1](out)

        return out
