!pip install gensim
!pip install keras==2.2.4
import os
import pandas as pd
from tqdm.autonotebook import *
from sklearn.decomposition import LatentDirichletAllocation

from sklearn.metrics import accuracy_score
import time
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack
from sklearn.model_selection import StratifiedKFold
from gensim.models import FastText, Word2Vec
import re
from keras.layers import *
from keras.models import *
from keras.preprocessing.text import Tokenizer, text_to_word_sequence
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing import text, sequence
from keras.callbacks import *
from keras.layers.advanced_activations import LeakyReLU, PReLU
import keras.backend as K
from keras.optimizers import *
from keras.utils import to_categorical
import tensorflow as tf
#import tensorflow.compat.v1 as tf #2.1
#tf.disable_v2_behavior()#2.1

import random as rn
import gc
import logging
import gensim

#from tensorflow.contrib.rnn import *
os.environ['PYTHONHASHSEED'] = '0'
# 显卡使用（如没显卡需要注释掉）
os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
np.random.seed(1024)
rn.seed(1024)
tf.set_random_seed(1024)
#tf.random.set_seed(1024)##2.1
#path="data/"
#os.listdir("data/")
#################################gpu22222222222222222222222#################

def get_age_data():
    train_user = pd.read_csv('train_preliminary/user.csv')
    train_final_user = pd.read_csv('train_semi_final/user.csv')
    test_data = test_data = pd.DataFrame({"user_id":(np.arange(3000001, 4000001, 1)), "age":"-1", "gender":"-1"})
    data = pd.concat([train_user,train_final_user, test_data], axis=0, sort=False)
    del train_user,train_final_user,test_data
    gc.collect()
    return data
data= get_age_data()
data = data.sort_values(by=['user_id']).reset_index(drop=True)
###############################################
emb1=np.load('256_w2c/w2v_256_creative_id_xuli95_win15iter8_emb.npy')
emb3=np.load('256_w2c/w2v_256_advertiser_id_xuli95_win15iter8.npy')
emb6=np.load('256_w2c/w2v_256_ad_id_xuli95_win15iter8_emb.npy')

x1=np.load('256_w2c/x1_xulie95_creative_id_win15iter8.npy')
x3=np.load('256_w2c/x5_xulie95_advertiser_id_win15iter8.npy')
x6=np.load('256_w2c/x3_xulie95_ad_id_win15iter8.npy')
 
emb1=emb1.astype(np.float32)
emb3=emb3.astype(np.float32)
emb6=emb6.astype(np.float32)

train_data = data[data['age']!='-1']
#train_data = data[data['gender']!='-1']

train_input_1 = x1[:len(train_data)]
test_input_1 = x1[len(train_data):]
train_input_3 = x3[:len(train_data)]
test_input_3 = x3[len(train_data):]
train_input_6 = x6[:len(train_data)]
test_input_6 = x6[len(train_data):]

label = to_categorical(train_data['age'] - 1)
#label = to_categorical(train_data['gender'] - 1)

gc.collect()

#增强序列
x11=np.load('256_w2c/x1_xulie95_creative_id_reset_user_time_win15iter8.npy')
x33=np.load('256_w2c/x5_xulie95_advertiser_id_reset_user_time_win15iter8.npy')
x66=np.load('256_w2c/x3_xulie95_ad_id_reset_user_time_win15iter8.npy')

train_input_11 = x11[:len(train_data)]
test_input_11 = x11[len(train_data):]

train_input_33 = x33[:len(train_data)]
test_input_33 = x33[len(train_data):]

train_input_66 = x66[:len(train_data)]
test_input_66 = x66[len(train_data):]
del x1,x3,x6,x11,x33,x66

gc.collect()

#tfidf
import pickle
with open('tfidf/final_tfidf11_creative_id_age.pkl', 'rb') as f:###############路径！！
    f1 = pickle.load(f)    
with open('tfidf/final__tfidf11_ad_id_age.pkl', 'rb') as f:
    f2 = pickle.load(f)
with open('tfidf/final__tfidf11_advertiser_id_age.pkl', 'rb') as f:    
    f3 = pickle.load(f)
with open('tfidf/final_count11__ad_id_age.pkl', 'rb') as f:
    f4 = pickle.load(f)    
with open('tfidf/final_count11_advertiser_id_age.pkl', 'rb') as f:
    f5 = pickle.load(f)
with open('tfidf/final_count11_creative_id_age.pkl', 'rb') as f:    
    f6 = pickle.load(f) 
#with open('age_model/final_target_4id_1age.pkl', 'rb') as f:    
#    f7 = pickle.load(f) 
with open('age_model/final_target_5id_37age.pkl', 'rb') as f:    
    f7 = pickle.load(f)     
feature = pd.concat([f1,f2, f3,f4,f5,f6,f7], axis=1, sort=False)
del f1,f2, f3,f4,f5,f6 ,f7    
#feature = pd.concat([f1,f2, f3], axis=1, sort=False)

feature = feature.fillna(-1)
from sklearn.preprocessing import StandardScaler
ss=StandardScaler()
ss.fit(feature)
hin_feature = ss.transform(feature)
num_feature_input = hin_feature.shape[1]

train_input_5 = hin_feature[:len(train_data)]
test_input_5 = hin_feature[len(train_data):]
del feature,hin_feature
gc.collect()

###########
# 需要用到的函数
class AdamW(Optimizer):
    def __init__(self, lr=0.001, beta_1=0.9, beta_2=0.999, weight_decay=1e-4,  # decoupled weight decay (1/4)
                 epsilon=1e-8, decay=0., **kwargs):
        super(AdamW, self).__init__(**kwargs)
        with K.name_scope(self.__class__.__name__):
            self.iterations = K.variable(0, dtype='int64', name='iterations')
            self.lr = K.variable(lr, name='lr')
            self.beta_1 = K.variable(beta_1, name='beta_1')
            self.beta_2 = K.variable(beta_2, name='beta_2')
            self.decay = K.variable(decay, name='decay')
            # decoupled weight decay (2/4)
            self.wd = K.variable(weight_decay, name='weight_decay')
        self.epsilon = epsilon
        self.initial_decay = decay

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        self.updates = [K.update_add(self.iterations, 1)]
        wd = self.wd  # decoupled weight decay (3/4)

        lr = self.lr
        if self.initial_decay > 0:
            lr *= (1. / (1. + self.decay * K.cast(self.iterations,
                                                  K.dtype(self.decay))))

        t = K.cast(self.iterations, K.floatx()) + 1
        lr_t = lr * (K.sqrt(1. - K.pow(self.beta_2, t)) /
                     (1. - K.pow(self.beta_1, t)))

        ms = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
        vs = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
        self.weights = [self.iterations] + ms + vs

        for p, g, m, v in zip(params, grads, ms, vs):
            m_t = (self.beta_1 * m) + (1. - self.beta_1) * g
            v_t = (self.beta_2 * v) + (1. - self.beta_2) * K.square(g)
            # decoupled weight decay (4/4)
            p_t = p - lr_t * m_t / (K.sqrt(v_t) + self.epsilon) - lr * wd * p

            self.updates.append(K.update(m, m_t))
            self.updates.append(K.update(v, v_t))
            new_p = p_t

            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'beta_1': float(K.get_value(self.beta_1)),
                  'beta_2': float(K.get_value(self.beta_2)),
                  'decay': float(K.get_value(self.decay)),
                  'weight_decay': float(K.get_value(self.wd)),
                  'epsilon': self.epsilon}
        base_config = super(AdamW, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


from keras.engine.topology import Layer
class Attention(Layer):
    def __init__(self, step_dim,
                 W_regularizer=None, b_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, **kwargs):
        self.supports_masking = True
        self.init = initializers.get('glorot_uniform')

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.step_dim = step_dim
        self.features_dim = 0
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        assert len(input_shape) == 3

        self.W = self.add_weight((input_shape[-1],),
                                 initializer=self.init,
                                 name='{}_W'.format(self.name),
                                 regularizer=self.W_regularizer,
                                 constraint=self.W_constraint)
        self.features_dim = input_shape[-1]

        if self.bias:
            self.b = self.add_weight((input_shape[1],),
                                     initializer='zero',
                                     name='{}_b'.format(self.name),
                                     regularizer=self.b_regularizer,
                                     constraint=self.b_constraint)
        else:
            self.b = None

        self.built = True

    def compute_mask(self, input, input_mask=None):
        return None

    def call(self, x, mask=None):
        features_dim = self.features_dim
        step_dim = self.step_dim

        eij = K.reshape(K.dot(K.reshape(x, (-1, features_dim)),
                        K.reshape(self.W, (features_dim, 1))), (-1, step_dim))

        if self.bias:
            eij += self.b

        eij = K.tanh(eij)

        a = K.exp(eij)

        if mask is not None:
            a *= K.cast(mask, K.floatx())

        a /= K.cast(K.sum(a, axis=1, keepdims=True) + K.epsilon(), K.floatx())

        a = K.expand_dims(a)
        weighted_input = x * a
        return K.sum(weighted_input, axis=1)

    def compute_output_shape(self, input_shape):
        return input_shape[0],  self.features_dim

#########
from tensorflow.keras import backend as K
import numpy as np
#from keras.callbacks import ModelCheckpoint,TensorBoard
class CyclicLR(Callback):
    def __init__(self, base_lr=0.001, max_lr=0.006, step_size=2000., mode='triangular',
                 gamma=1., scale_fn=None, scale_mode='cycle'):
        super(CyclicLR, self).__init__()

        self.base_lr = base_lr
        self.max_lr = max_lr
        self.step_size = step_size
        self.mode = mode
        self.gamma = gamma
        if scale_fn == None:
            if self.mode == 'triangular':
                self.scale_fn = lambda x: 1.
                self.scale_mode = 'cycle'
            elif self.mode == 'triangular2':
                self.scale_fn = lambda x: 1/(2.**(x-1))
                self.scale_mode = 'cycle'
            elif self.mode == 'exp_range':
                self.scale_fn = lambda x: gamma**(x)
                self.scale_mode = 'iterations'
        else:
            self.scale_fn = scale_fn
            self.scale_mode = scale_mode
        self.clr_iterations = 0.
        self.trn_iterations = 0.
        self.history = {}

        self._reset()

    def _reset(self, new_base_lr=None, new_max_lr=None,
               new_step_size=None):
        """Resets cycle iterations.
        Optional boundary/step size adjustment.
        """
        if new_base_lr != None:
            self.base_lr = new_base_lr
        if new_max_lr != None:
            self.max_lr = new_max_lr
        if new_step_size != None:
            self.step_size = new_step_size
        self.clr_iterations = 0.
        
    def clr(self):
        cycle = np.floor(1+self.clr_iterations/(2*self.step_size))
        x = np.abs(self.clr_iterations/self.step_size - 2*cycle + 1)
        if self.scale_mode == 'cycle':
            return self.base_lr + (self.max_lr-self.base_lr)*np.maximum(0, (1-x))*self.scale_fn(cycle)
        else:
            return self.base_lr + (self.max_lr-self.base_lr)*np.maximum(0, (1-x))*self.scale_fn(self.clr_iterations)
        
    def on_train_begin(self, logs={}):
        logs = logs or {}

        if self.clr_iterations == 0:
            K.set_value(self.model.optimizer.lr, self.base_lr)
        else:
            K.set_value(self.model.optimizer.lr, self.clr())        
            
    def on_batch_end(self, epoch, logs=None):
        
        logs = logs or {}
        self.trn_iterations += 1
        self.clr_iterations += 1

        self.history.setdefault('lr', []).append(K.get_value(self.model.optimizer.lr))
        self.history.setdefault('iterations', []).append(self.trn_iterations)

        for k, v in logs.items():
            self.history.setdefault(k, []).append(v)
        
        K.set_value(self.model.optimizer.lr, self.clr())
        
from sklearn.model_selection import KFold
skf = KFold(n_splits=5, shuffle=True, random_state=2020)
for i, (train_index, test_index) in enumerate(skf.split(train_input_5, train_data['age'].astype('int'))):
    if(i==0):
        num0_train=train_index
        num0_test=test_index
    elif(i==1):
        num1_train=train_index
        num1_test=test_index
    elif(i==2):
        num2_train=train_index
        num2_test=test_index
    elif(i==3):
        num3_train=train_index
        num3_test=test_index
    elif(i==4):
        num4_train=train_index
        num4_test=test_index
    del train_index, test_index
gc.collect()    

def model_conv(emb1, emb3, emb6, num_feature_input): #emb3,  , num_feature_input
    K.clear_session()
    emb_layer_1 = Embedding(
        input_dim=emb1.shape[0],
        output_dim=emb1.shape[1],
        weights=[emb1],
        input_length=95,###30
        trainable=False
    )   
    emb_layer_3 = Embedding(
        input_dim=emb3.shape[0],
        output_dim=emb3.shape[1],
        weights=[emb3],
        input_length=95,
        trainable=False
    )    
    emb_layer_6 = Embedding(
        input_dim=emb6.shape[0],
        output_dim=emb6.shape[1],
        weights=[emb6],
        input_length=95,
        trainable=False
    ) 
    seq1 = Input(shape=(95,))#####30
    seq3 = Input(shape=(95,))        
    seq6 = Input(shape=(95,))    
    x1 = emb_layer_1(seq1)
    x3 = emb_layer_3(seq3)    
    x6 = emb_layer_6(seq6)
    #del emb1,emb3,emb6
    #gc.collect()

    sdrop=SpatialDropout1D(rate=0.2)
    x1 = sdrop(x1)
    x3 = sdrop(x3)
    x6 = sdrop(x6)
    x11 = concatenate([x1,x3,x6] , axis=-1)           
    x = Dropout(0.4)(Bidirectional(CuDNNLSTM(300, return_sequences=True))(x11))       
    x = Dense(256, activation='relu')(x)
    semantic = TimeDistributed(Dense(128, activation="tanh"))(x)
    
    merged_1 = Lambda(lambda x: K.max(x, axis=1), output_shape=(128,))(semantic)
    merged_1_avg = Lambda(lambda x: K.mean(x, axis=1), output_shape=(128,))(semantic)
    hin = Input(shape=(num_feature_input, ))
    htime = Dense(160)(hin)
    x = concatenate([merged_1,  merged_1_avg, htime])
    
    x = Dropout(0.4)(Activation(activation="relu")(BatchNormalization()(Dense(1000)(x))))
    x = Activation(activation="relu")(BatchNormalization()(Dense(500)(x)))

    
    pred = Dense(10, activation='softmax')(x)######10
    #pred = Dense(2, activation='softmax')(x)
    model = Model(inputs=[seq1, seq3, seq6,hin], outputs=pred)

    from keras.utils import multi_gpu_model
    model = multi_gpu_model(model, 2)
    model.compile(loss='categorical_crossentropy',
                  optimizer=AdamW(lr=0.001,weight_decay=0.06,),metrics=["accuracy"])
    return model
gc.collect()
######一折
model_age = model_conv(emb1, emb3,emb6,num_feature_input)


def dataloader(test_index):

    x1_va = np.array(train_input_1)[test_index] 

    x3_va = np.array(train_input_3)[test_index]#########
    x6_va = np.array(train_input_6)[test_index]#########

    x11_va =np.array(train_input_11)[test_index] 
    x33_va =np.array(train_input_33)[test_index]#########
    x66_va =np.array(train_input_66)[test_index]#########
    
    x5_va = np.array(train_input_5)[test_index]
    y_va =label[test_index]
    gc.collect()
    return x1_va, x3_va,x6_va, x5_va,x11_va, x33_va,x66_va,y_va

sub = np.zeros((test_input_1.shape[0], 10))###########################2
oof_pred = np.zeros((train_input_1.shape[0], 10))###########################2
oof_pred_da = np.zeros((train_input_1.shape[0], 10))###########################10
sub_da = np.zeros((test_input_1.shape[0], 10)) ###########################10

startload = time.time()

filepath = "age_model_adid1_count3/nn_v1_atten2020_5idcode_0.h5" 
model_age.load_weights(filepath)
x1_va, x3_va,x6_va, x5_va,x11_va, x33_va,x66_va ,y_va=dataloader(num0_test)

oof_pred[num0_test] = model_age.predict([x1_va, x3_va,x6_va, x5_va],batch_size=1024,verbose=1)###2048
sub += model_age.predict([test_input_1, test_input_3,test_input_6,test_input_5],batch_size=1024,verbose=1)/skf.n_splits##   
oof_pred_da[num0_test] = model_age.predict([x11_va, x33_va,x66_va, x5_va],batch_size=1024,verbose=1)
sub_da += model_age.predict([test_input_11, test_input_33,test_input_66,test_input_5],batch_size=1024,verbose=1)/skf.n_splits
    
filepath = "age_model_adid1_count3/nn_v1_atten2020_5idcode_1.h5" 
model_age.load_weights(filepath)
x1_va, x3_va,x6_va, x5_va,x11_va, x33_va,x66_va ,y_va=dataloader(num1_test)

oof_pred[num1_test] = model_age.predict([x1_va, x3_va,x6_va, x5_va],batch_size=1024,verbose=1)###2048
sub += model_age.predict([test_input_1, test_input_3,test_input_6,test_input_5],batch_size=1024,verbose=1)/skf.n_splits##
oof_pred_da[num1_test] = model_age.predict([x11_va, x33_va,x66_va, x5_va],batch_size=1024,verbose=1)
sub_da += model_age.predict([test_input_11, test_input_33,test_input_66,test_input_5],batch_size=1024,verbose=1)/skf.n_splits
###########################


filepath = "age_model_adid1_count3/nn_v1_atten2020_5idcode_2.h5" 
model_age.load_weights(filepath)
x1_va, x3_va,x6_va, x5_va,x11_va, x33_va,x66_va ,y_va=dataloader(num2_test)

oof_pred[num2_test] = model_age.predict([x1_va, x3_va,x6_va, x5_va],batch_size=1024,verbose=1)###2048
sub += model_age.predict([test_input_1, test_input_3,test_input_6,test_input_5],batch_size=1024,verbose=1)/skf.n_splits##
oof_pred_da[num2_test] = model_age.predict([x11_va, x33_va,x66_va, x5_va],batch_size=1024,verbose=1)
sub_da += model_age.predict([test_input_11, test_input_33,test_input_66,test_input_5],batch_size=1024,verbose=1)/skf.n_splits
 ###########################   
    
filepath = "age_model_adid1_count3/nn_v1_atten2020_5idcode_3.h5" 
model_age.load_weights(filepath)
x1_va, x3_va,x6_va, x5_va,x11_va, x33_va,x66_va ,y_va=dataloader(num3_test)

oof_pred[num3_test] = model_age.predict([x1_va, x3_va,x6_va, x5_va],batch_size=1024,verbose=1)###2048
sub += model_age.predict([test_input_1, test_input_3,test_input_6,test_input_5],batch_size=1024,verbose=1)/skf.n_splits##
oof_pred_da[num3_test] = model_age.predict([x11_va, x33_va,x66_va, x5_va],batch_size=1024,verbose=1)
sub_da += model_age.predict([test_input_11, test_input_33,test_input_66,test_input_5],batch_size=1024,verbose=1)/skf.n_splits
###########################

filepath = "age_model_adid1_count3/nn_v1_atten2020_5idcode_4.h5" 
model_age.load_weights(filepath)
x1_va, x3_va,x6_va, x5_va,x11_va, x33_va,x66_va ,y_va=dataloader(num4_test)

oof_pred[num4_test] = model_age.predict([x1_va, x3_va,x6_va, x5_va],batch_size=1024,verbose=1)###2048
sub += model_age.predict([test_input_1, test_input_3,test_input_6,test_input_5],batch_size=1024,verbose=1)/skf.n_splits##
oof_pred_da[num4_test] = model_age.predict([x11_va, x33_va,x66_va, x5_va],batch_size=1024,verbose=1)
sub_da += model_age.predict([test_input_11, test_input_33,test_input_66,test_input_5],batch_size=1024,verbose=1)/skf.n_splits
    
endload = time.time() - startload
print('加载时间：%.2fmin' % (endload / 60))

score1=accuracy_score(np.argmax((label),axis=1)+1, np.argmax((oof_pred),axis=1)+1)
score2=accuracy_score(np.argmax((label),axis=1)+1, np.argmax((oof_pred_da),axis=1)+1)
score=accuracy_score(np.argmax((label),axis=1)+1, np.argmax((oof_pred_da+oof_pred),axis=1)+1)

aa=sub+sub_da
test = data[data['age'] =='-1']
submit = test[['user_id']]
submit.columns = ['user_id']
submit['predicted_age'] = aa.argmax(1)+1

#五折
oof = np.concatenate((oof_pred,sub))
oof = pd.DataFrame(oof)
oof.columns = [str(i+1) for i in range(10)]
oof['id'] = pd.concat([train_data[['user_id']],test[['user_id']]])['user_id'].values
#oof.to_csv("sub/wuzhe_submission_nn_gender3_1input_fc256_drop0.4_bn0.4_datatime_relr_{}.csv".format(np.mean(score)),index=False) #v1_test.csv
np.save("age_model/wuzhe_submission_nn_age3_adid1_count3_datatime_relr_{}.npy".format(np.mean(score1)), oof)

#五折
oof1 = np.concatenate((oof_pred_da,sub_da))
oof1 = pd.DataFrame(oof1)
oof1.columns = [str(i+1) for i in range(10)]
oof1['id'] = pd.concat([train_data[['user_id']],test[['user_id']]])['user_id'].values
#oof1.to_csv("sub/wuzhe_submission_nn_gender3_1input_fc256_drop0.4_bn0.4_datatime_relr_dastr_{}.csv".format(np.mean(score)),index=False) #v1_test.csv
np.save("age_model/wuzhe_submission_nn_age3_adid1_count3_datatime_relr_dastr_{}.npy".format(np.mean(score2)), oof1)
